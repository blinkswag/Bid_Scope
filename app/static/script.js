// scripts.js
function showSuggestions() {
    const suggestionContainer = document.getElementById('suggestionContainer');
    suggestionContainer.style.display = suggestionContainer.style.display === 'none' ? 'block' : 'none';
}

function selectSuggestion(suggestion) {
    const messageInput = document.getElementById('messageInput');
    messageInput.value = suggestion;
    const suggestionContainer = document.getElementById('suggestionContainer');
    suggestionContainer.style.display = 'none';
}

// Existing functions for chat functionality
$(document).ready(function() {
    $('#chatForm').submit(function(event) {
        event.preventDefault();
        var messageText = $('#messageInput').val();
        if (messageText.trim() === '') {
            return;
        }

        var threadId = $('#threadId').val();
        if (!threadId) {
            createNewThreadAndSendMessage(messageText);
        } else {
            sendMessage(messageText, threadId);
        }
    });

    function createNewThreadAndSendMessage(messageText) {
        $.ajax({
            type: 'POST',
            url: '/new-chat',
            success: function(response) {
                var threadId = response.thread_id;
                localStorage.setItem('current_thread_id', threadId);
                $('#threadId').val(threadId);
                sendMessage(messageText, threadId);
                newChatPending = false;
            },
            error: function() {
                alert('Failed to start a new chat.');
            }
        });
    }

    function sendMessage(messageText, threadId) {
        var formData = new FormData($('#chatForm')[0]);
        formData.append('message', messageText);
        formData.append('thread_id', threadId);
        $('#chatWindow').append('<div class="message-container user"><div class="message user-message">' + messageText + '</div><img src="static/User.png" class="avatar"></div>');
        $('#messageInput').val('');
        var loadingElementId = 'loadingMessage' + Date.now();
        var loadingHtml = '<div id="' + loadingElementId + '" class="message-container bot"><img src="static/blinksigns_logo.jpg" class="avatar"><div class="message bot-response"><img src="static/wait.gif" style="width:50px;height:50px;"></div></div>';
        $('#chatWindow').append(loadingHtml);
        scrollToBottom();
        $.ajax({
            type: 'POST',
            url: '/',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#' + loadingElementId).remove();
                $('#chatWindow').append('<div class="message-container bot"><img src="static/blinksigns_logo.jpg" class="avatar"><div class="message bot-response">' + response.message + '</div></div>');
                scrollToBottom();
            },
            error: function() {
                $('#' + loadingElementId).remove();
                $('#chatWindow').append('<div class="message-container bot"><img src="static/blinksigns_logo.jpg" class="avatar"><div class="message bot-response">Failed to send message.</div></div>');
                scrollToBottom();
            }
        });
    }
    function handleResize() {
        if ($(window).width() < 768) {
            // Adjust for small screens
            $('.main-container').css('flex-direction', 'column');
            $('.sidebar').css('flex', '0 0 100%');
            $('.chat-container').css('margin', '5px');
        } else {
            // Adjust for larger screens
            $('.main-container').css('flex-direction', 'row');
            $('.sidebar').css('flex', '0 0 25%');
            $('.chat-container').css('margin', '10px');
        }
    }

    $(window).resize(handleResize);
    handleResize();

    function scrollToBottom() {
        $('#chatWindow').animate({ scrollTop: $('#chatWindow')[0].scrollHeight }, 1000);
    }

    // Add click event to thread buttons
    $('button[onclick^="loadThread"]').on('click', function() {
        var threadId = $(this).attr('onclick').match(/'([^']+)'/)[1];
        loadThread(threadId);
    });
});
