$(document).ready(function() {

    let currentUserId = $('#buddyList').data('current-user-id');
    let selectedBuddyId = null;
    let mediaRecorder = null;
    let audioChunks = [];
    let streamRef = null;  // Store stream reference to stop it properly!

    // Function to load messages
    function loadMessages(buddyId) {
        $('#chatMessages').empty();
        $.ajax({
            url: `/get_messages/${buddyId}`,
            type: 'GET',
            success: function(response) {
                response.forEach(msg => {
                    const messageClass = msg.sender_id == currentUserId ? 'sent' : 'received';
                    let displayMessage = '';

                    if (msg.message.startsWith('File:')) {
                        const filename = msg.message.replace('File: ', '');
                        displayMessage = `<a href="/static/uploads/${filename}" target="_blank" download>📎 ${filename}</a>`;
                    } else if (msg.message.startsWith('Voice:')) {
                        const filename = msg.message.replace('Voice: ', '');
                        displayMessage = `<audio controls><source src="/static/uploads/${filename}" type="audio/webm"></audio>`;
                    } else {
                        displayMessage = msg.message;
                    }

                    $('#chatMessages').append(
                        `<div class="message ${messageClass}">${displayMessage}</div>`
                    );
                });

                $('#chatMessages').scrollTop($('#chatMessages')[0].scrollHeight);
            },
            error: function() {
                alert('Error loading messages!');
            }
        });
    }

    // Auto-load first buddy chat
    let firstBuddy = $('.buddy').first();
    if (firstBuddy.length) {
        firstBuddy.addClass('active');
        selectedBuddyId = firstBuddy.data('buddy-id');
        $('#chat-buddy').text(firstBuddy.text());
        loadMessages(selectedBuddyId);
    }

    // When buddy clicked
    $('.buddy').click(function(e) {
        e.preventDefault();
        $('.buddy').removeClass('active');
        $(this).addClass('active');
        selectedBuddyId = $(this).data('buddy-id');
        $('#chat-buddy').text($(this).text());
        loadMessages(selectedBuddyId);
    });

    // Send Text Message
    $('#sendButton').click(function() {
        const message = $('#messageInput').val().trim();
        if (message === "" || !selectedBuddyId) return;

        $.ajax({
            url: '/send_message',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                receiver_id: selectedBuddyId,
                message: message
            }),
            success: function(response) {
                if (response.status === 'Message sent') {
                    $('#chatMessages').append(
                        `<div class="message sent">${message}</div>`
                    );
                    $('#messageInput').val('');
                    $('#chatMessages').scrollTop($('#chatMessages')[0].scrollHeight);
                } else {
                    alert('Failed to send message.');
                }
            },
            error: function() {
                alert('Error sending message!');
            }
        });
    });

    // File attachment
    $('#attachButton').click(function() {
        $('#fileInput').click();
    });

    $('#fileInput').change(function() {
        const file = this.files[0];
        if (file && selectedBuddyId) {
            const formData = new FormData();
            formData.append('receiver_id', selectedBuddyId);
            formData.append('file', file);

            $.ajax({
                url: '/send_file',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.status === 'File sent') {
                        $('#chatMessages').append(
                            `<div class="message sent"><a href="/static/uploads/${response.filename}" target="_blank" download>📎 ${file.name}</a></div>`
                        );
                        $('#chatMessages').scrollTop($('#chatMessages')[0].scrollHeight);
                    } else {
                        alert('Failed to send file.');
                    }
                },
                error: function() {
                    alert('Error sending file!');
                }
            });
        }
    });

    // ======================

    // 🎤 RECORD BUTTON
    // 🎤 RECORD BUTTON
    $('#recordButton').click(function() {
        console.log("🎤 Mic button clicked!");
        $('#statusText').text("Recording...").show();  // <-- Visual Feedback
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                streamRef = stream;
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.start();
                console.log("🎙️ Recording started!");

                mediaRecorder.ondataavailable = e => {
                    audioChunks.push(e.data);
                };

                mediaRecorder.onstop = () => {
                    console.log("🛑 Recording stopped.");
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    $('#audioPlayer').attr('src', audioUrl).show();
                    $('#sendRecordButton').show();
                    $('#statusText').hide();

                    // Stop mic
                    stream.getTracks().forEach(track => track.stop());
                };

                // Update UI
                $('#recordButton').hide();
                $('#stopRecordButton').show();
                $('#sendRecordButton').hide();
            })
            .catch(err => {
                console.error("❌ Microphone error:", err);
                alert('Microphone permission denied or error! Please check browser permissions.');
                $('#statusText').hide();
            });
    });

    
    // ⏹️ STOP BUTTON
    $('#stopRecordButton').click(function() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            $('#stopRecordButton').hide();
        }
    });

    // ✅ SEND BUTTON
    $('#sendRecordButton').click(function() {
        if (audioChunks.length === 0 || !selectedBuddyId) {
            alert('No audio recorded or no buddy selected!');
            return;
        }

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('receiver_id', selectedBuddyId);
        formData.append('audio', audioBlob, 'voice_message.webm');

        $.ajax({
            url: '/send_voice',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                alert('Voice message sent!');
                $('#recordButton').show();
                $('#sendRecordButton').hide();
                $('#audioPlayer').hide();
                audioChunks = [];

                if (response.filename) {
                    $('#chatMessages').append(
                        `<div class="message sent"><audio controls><source src="/static/uploads/${response.filename}" type="audio/webm"></audio></div>`
                    );
                    $('#chatMessages').scrollTop($('#chatMessages')[0].scrollHeight);
                }
            },
            error: function() {
                alert('Error sending voice!');
            }
        });
    });




});
