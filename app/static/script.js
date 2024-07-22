$(document).ready(function() {
    function adjustThreadContainerHeight() {
        const sidebarHeight = $('.sidebar').height();
        const profileSectionHeight = $('.profile-section').outerHeight(true);
        const logoutButtonHeight = $('.logout-button').outerHeight(true);
        let buttonHeights = 0;

        // Calculate the total height of all cssbuttons-io-button elements
        $('.cssbuttons-io-button').each(function() {
            buttonHeights += $(this).outerHeight(true);
        });

        const availableHeight = sidebarHeight - (profileSectionHeight + logoutButtonHeight + buttonHeights + 40); // Adjust for padding/margin
        $('.thread-container').css('height', availableHeight + 'px');
    }

    // Adjust height on page load and window resize
    adjustThreadContainerHeight();
    $(window).resize(adjustThreadContainerHeight);

    // Existing functions for chat functionality
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
            $('.sidebar').css('width', '100%');
            $('.chat-container').css('margin', '5px');
        } else if ($(window).width() < 992) {
            // Adjust for medium screens
            $('.sidebar').css('width', '30%');
            $('.main-container').css('flex-direction', 'row');
            $('.chat-container').css('margin', '10px');
        } else if ($(window).width() < 1200) {
            // Adjust for large screens
            $('.sidebar').css('width', '25%');
            $('.main-container').css('flex-direction', 'row');
            $('.chat-container').css('margin', '10px');
        } else {
            // Adjust for extra large screens
            $('.sidebar').css('width', '20%');
            $('.main-container').css('flex-direction', 'row');
            $('.chat-container').css('margin', '10px');
        }
        adjustThreadContainerHeight();
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
