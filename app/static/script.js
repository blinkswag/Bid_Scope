$(document).ready(function () {
    let resizeTimeout;

    function adjustThreadContainerHeight() {
        const sidebarHeight = $('.sidebar').height();
        const profileSectionHeight = $('.profile-section').outerHeight(true);
        const logoutButtonHeight = $('.logout-button').outerHeight(true);
        let buttonHeights = 0;

        $('.cssbuttons-io-button').each(function () {
            buttonHeights += $(this).outerHeight(true);
        });

        const availableHeight = sidebarHeight - (profileSectionHeight + logoutButtonHeight + buttonHeights + 40);
        $('.thread-container').css('height', availableHeight + 'px');
    }

    // Debounce resize event to prevent multiple rapid triggers
    function debounceResize() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(adjustThreadContainerHeight, 250);
    }

    $(window).resize(debounceResize);

    // Optimize scroll to bottom with requestAnimationFrame for smoother experience
    function scrollToBottom() {
        requestAnimationFrame(() => {
            $('#chatWindow').scrollTop($('#chatWindow')[0].scrollHeight);
        });
    }

    adjustThreadContainerHeight();

    // Handle message submission
    $('#chatForm').submit(async function (event) {
        event.preventDefault();
        const messageText = $('#messageInput').val().trim();
        if (!messageText) return;

        const threadId = $('#threadId').val();
        if (!threadId) {
            await createNewThreadAndSendMessage(messageText);
        } else {
            await sendMessage(messageText, threadId);
        }
    });

    async function createNewThreadAndSendMessage(messageText) {
        try {
            const response = await $.post('/new-chat');
            const threadId = response.thread_id;
            localStorage.setItem('current_thread_id', threadId);
            $('#threadId').val(threadId);
            await sendMessage(messageText, threadId);
        } catch (error) {
            alert('Failed to start a new chat.');
        }
    }

    async function sendMessage(messageText, threadId) {
        const formData = new FormData($('#chatForm')[0]);
        formData.append('message', messageText);
        formData.append('thread_id', threadId);

        // Append user message immediately for instant feedback
        $('#chatWindow').append(`
            <div class="message-container user">
                <div class="message user-message">${messageText}</div>
                <img src="static/User.png" class="avatar">
            </div>
        `);
        $('#messageInput').val('');

        const loadingElementId = 'loadingMessage' + Date.now();
        const loadingHtml = `
            <div id="${loadingElementId}" class="message-container bot">
                <img src="static/blinksigns_logo.jpg" class="avatar">
                <div class="message bot-response">
                    <img src="static/wait.gif" style="width:50px;height:50px;"> Bid Bot Thinking...
                </div>
            </div>
        `;
        $('#chatWindow').append(loadingHtml);
        scrollToBottom();

        try {
            const response = await $.ajax({
                type: 'POST',
                url: '/',
                data: formData,
                processData: false,
                contentType: false
            });
            $('#' + loadingElementId).remove();
            $('#chatWindow').append(`
                <div class="message-container bot">
                    <img src="static/blinksigns_logo.jpg" class="avatar">
                    <div class="message bot-response">${response.message}</div>
                </div>
            `);
            scrollToBottom();
        } catch (error) {
            $('#' + loadingElementId).remove();
            $('#chatWindow').append(`
                <div class="message-container bot">
                    <img src="static/blinksigns_logo.jpg" class="avatar">
                    <div class="message bot-response">Failed to send message.</div>
                </div>
            `);
            scrollToBottom();
        }
    }

    // Optimized file upload handling
    $('#fileUpload').on('change', async function () {
        const files = $(this).prop('files');
        if (!files || files.length === 0) return;

        $('#messageInput, #fileUpload, .send-button').prop('disabled', true);

        const threadId = $('#threadId').val();
        if (!threadId) {
            await createNewThreadAndProcessFiles(files);
        } else {
            await processFiles(0, files, threadId);
        }
    });

    async function createNewThreadAndProcessFiles(files) {
        try {
            const response = await $.post('/new-chat');
            const threadId = response.thread_id;
            localStorage.setItem('current_thread_id', threadId);
            $('#threadId').val(threadId);
            await processFiles(0, files, threadId);
        } catch (error) {
            alert('Failed to start a new chat.');
        }
    }

    async function processFiles(index, files, threadId) {
        if (index >= files.length) {
            $('#messageInput, #fileUpload, .send-button').prop('disabled', false);
            return;
        }

        const file = files[index];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('thread_id', threadId);

        const loadingElementId = 'loadingMessage' + Date.now();
        $('#chatWindow').append(`
            <div id="${loadingElementId}" class="message-container bot">
                <img src="static/blinksigns_logo.jpg" class="avatar">
                <div class="message bot-response">
                    <img src="static/upload.gif" style="width:50px;height:50px;"> Uploading File...
                </div>
            </div>
        `);
        scrollToBottom();

        try {
            const response = await $.ajax({
                type: 'POST',
                url: '/',
                data: formData,
                processData: false,
                contentType: false
            });

            $('#' + loadingElementId).remove();
            $('#chatWindow').append(`
                <div class="message-container bot">
                    <img src="static/blinksigns_logo.jpg" class="avatar">
                    <div class="message bot-response">${response.message}</div>
                </div>
            `);
            scrollToBottom();

            await processFiles(index + 1, files, threadId);
        } catch (error) {
            $('#' + loadingElementId).remove();
            $('#chatWindow').append(`
                <div class="message-container bot">
                    <img src="static/blinksigns_logo.jpg" class="avatar">
                    <div class="message bot-response">Failed to upload file.</div>
                </div>
            `);
            scrollToBottom();
            await processFiles(index + 1, files, threadId);
        }
    }

    // Handle screen resizing and layout adjustments
    function handleResize() {
        if ($(window).width() < 768) {
            $('.main-container').css('flex-direction', 'column');
            $('.sidebar').css('width', '100%');
            $('.chat-container').css('margin', '5px');
        } else {
            $('.sidebar').css('width', $(window).width() < 992 ? '30%' : '20%');
            $('.main-container').css('flex-direction', 'row');
            $('.chat-container').css('margin', '10px');
        }
        adjustThreadContainerHeight();
    }

    $(window).resize(debounceResize);
    handleResize();

    // Load thread messages when a thread is clicked
    $('body').on('click', '.load-thread', function () {
        const threadId = $(this).data('thread-id');
        loadThread(threadId);
    });

    async function loadThread(threadId) {
        $('#chatWindow').html('<div class="loading-spinner">Loading...</div>');  // Show loading spinner
        try {
            const response = await $.get('/get-thread-messages', { thread_id: threadId });
            $('#chatWindow').empty();
            response.messages.forEach(msg => {
                const messageClass = msg.role === 'user' ? 'user-message' : 'bot-response';
                const messageHtml = `
                    <div class="message-container ${msg.role}">
                        <img src="static/${msg.role === 'user' ? 'User.png' : 'blinksigns_logo.jpg'}" class="avatar">
                        <div class="message ${messageClass}">${msg.content}</div>
                    </div>
                `;
                $('#chatWindow').append(messageHtml);
            });
            $('#threadId').val(threadId);
            scrollToBottom();
        } catch (error) {
            alert('Failed to load thread messages.');
        }
    }
});
