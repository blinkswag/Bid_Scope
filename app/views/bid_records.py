# bid_records.py
from flask import render_template, session, redirect, url_for
from app.db import Database
from app.utils.helpers import check_user_role
import pandas as pd
import plotly.graph_objects as go
import json

db = Database()

def init_bid_records_views(app):
    @app.route('/bid-records')
    @check_user_role(['Super Admin', 'Admin', 'User'])
    def bid_records():
        if 'logged_in' not in session:
            return redirect(url_for('login'))

        records = list(db.bid_records_collection.find())
        total_bids = len(records)
        lead_converted_count = db.bid_records_collection.count_documents({"QUALIFICATION": "Lead converted"})
        deal_count = db.bid_records_collection.count_documents({"QUALIFICATION": "Create Deal"})
        open_status_count = db.bid_records_collection.count_documents({"status": "Open"})
        comment_record  = db.counter_collection.find_one({'name': 'comment_counter'})
        comment_value = comment_record['count']

        # Data processing
        df = pd.DataFrame(records)
        bid_status_distribution = df['status'].value_counts().to_dict()
        bid_type_distribution = df['Bid Type'].value_counts().to_dict()
        qualification_distribution = df['QUALIFICATION'].value_counts().to_dict()
        classification_distribution = df['classification'].value_counts().to_dict()
        category_distribution = df['category'].value_counts().to_dict()
        bids_per_user = df['username'].value_counts().to_dict()

        return render_template('bid_records.html', 
                                comment_value=comment_value,
                                records=records, 
                                lead_converted_count=lead_converted_count,
                                deal_count=deal_count,
                                total_bids=total_bids,
                                open_status_count=open_status_count,
                                bid_status_distribution=json.dumps(bid_status_distribution),
                                bid_type_distribution=json.dumps(bid_type_distribution),
                                qualification_distribution=json.dumps(qualification_distribution),
                                classification_distribution=json.dumps(classification_distribution),
                                category_distribution=json.dumps(category_distribution),
                                bids_per_user=json.dumps(bids_per_user))

    @app.route('/table')
    @check_user_role(['Super Admin', 'Admin', 'User'])
    def table():
        records = db.bid_records_collection.find()
        return render_template('table.html', records=records)

    @app.route('/forecast')
    @check_user_role(['Super Admin', 'Admin', 'User'])
    def forecast():


        return render_template('forecast.html')
