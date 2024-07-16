# app/views/zoho.py
from flask import request, jsonify, session
import requests
import logging
from app.model.chat_model import ChatModel
from app.db import Database
from bson import ObjectId
from app.utils.helpers import remove_bracketed_content

logger = logging.getLogger(__name__)
db = Database()

def init_zoho_views(app, token_manager):
    @app.route('/get_ticket_details', methods=['POST'])
    def get_ticket_details():
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        current_thread_id = data.get('current_thread_id')
        username = data.get('username')

        if not ticket_id:
            return jsonify({'error': 'Ticket ID is required'}), 400

        try:
            access_token = token_manager.get_access_token()
            logger.debug(f"Using access token: {access_token}")

            ticket_response = requests.get(
                f'https://desk.zoho.com/api/v1/tickets/{ticket_id}',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
            )

            logger.debug(f"Ticket response status: {ticket_response.status_code}")
            logger.debug(f"Ticket response content: {ticket_response.text}")

            if ticket_response.ok:
                ticket_details = ticket_response.json()
                logger.debug(f"Ticket details fetched: {ticket_details}")

                ticket_title = ticket_details.get('subject', 'No Title')

                user_id = session.get('user_id')
                user = db.users_collection.find_one({"_id": ObjectId(user_id)})
                thread_ids = user.get('threads', [])

                if not current_thread_id and thread_ids:
                    current_thread_id = thread_ids[0]['id']
                elif not current_thread_id:
                    chat_model = ChatModel(db=db)
                    thread = chat_model.create_thread(name=ticket_title)
                    db.update_user_threads(user_id, thread.id)
                    current_thread_id = thread.id
                    logger.info(f"Created new thread {current_thread_id} for user {user_id}")

                if current_thread_id:
                    result = db.threads_collection.update_one(
                        {"thread_id": current_thread_id},
                        {"$set": {"name": ticket_title}}
                    )
                    logger.info(f"Updated thread {current_thread_id} with title {ticket_title}")

                # Fetch the last bot response from the current thread
                last_bot_response = fetch_last_bot_response(current_thread_id, username)

                return jsonify({'thread_id': current_thread_id, 'ticket_details': ticket_details, 'last_bot_response': last_bot_response})
            else:
                logger.error(f"Failed to fetch ticket details: {ticket_response.text}")
                return jsonify({'error': 'Failed to fetch ticket details'}), 500

        except Exception as e:
            logger.error(f"Exception occurred while fetching ticket details: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/add_comment_to_ticket', methods=['POST'])
    def add_comment_to_ticket():
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        comment = data.get('comment')

        try:
            access_token = token_manager.get_access_token()

            url = f"https://desk.zoho.com/api/v1/tickets/{ticket_id}/comments"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            comment_data = {
                'content': comment
            }
            response = requests.post(url, headers=headers, json=comment_data)
            return jsonify(response.json())
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def fetch_last_bot_response(thread_id, username):
        try:
            chat_model = ChatModel(db=db)
            messages = chat_model.get_threads_messages(thread_id)
            for message in messages:
                if message['role'] == 'assistant':
                    # Remove bracketed content and format the response
                    cleaned_message = remove_bracketed_content(message['content'][0]['text']['value'])
                    formatted_message = format_message_as_html(cleaned_message)
                    return f"{formatted_message}"
        except Exception as e:
            logger.error(f"Failed to fetch last bot response: {str(e)}")
        return ''

    def format_message_as_html(message):
        if not message:
            return ''
        
        # Replace markdown-style headers and lists with HTML formatting
        return message.replace('### ', '<p>').replace('\n', '<br>')

