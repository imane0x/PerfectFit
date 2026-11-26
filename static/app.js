class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            fileInput: document.querySelector("#file-input"),
            fileUploadButton: document.querySelector("#file-upload"),
            fileUploadWrapper: document.querySelector(".file-upload-wrapper"),
            imgPreview: document.querySelector('.file-upload-wrapper img'),
            fileCancelUpload: document.querySelector("#file-cancel")
        };

        this.state = false;
        this.userData = {
            message: null,
            name: "User",
            file: {
                data: null,
                mime_type: null
            }
        };
        this.botData = {
            message: null,
            name: "PerfectFit",
            file: {
                data: null,
                mime_type: null
            }
        };
        this.messages = [];
     
        
    }

    display() {
        const { openButton, chatBox, sendButton, fileInput, fileUploadButton, fileCancelUpload } = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox));
        sendButton.addEventListener('click', () => this.onSendButton(chatBox));

        // Set up file input and upload button listeners
        fileInput.addEventListener("change", () => this.onFileChange(fileInput));
        fileUploadButton.addEventListener("click", () => fileInput.click());
        fileCancelUpload.addEventListener("click", () => {
            this.userData.file = {};
            this.clearImagePreview();
        });

        // Listen for Enter key to send message
        const textField = chatBox.querySelector('input');
        textField.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                this.onSendButton(chatBox);
            }
        });
    }

    toggleState(chatBox) {
        this.state = !this.state;
        chatBox.classList.toggle('chatbox--active', this.state);
    }

    onSendButton(chatBox) {
        const textField = chatBox.querySelector('input');
        const text1 = textField.value;

        // Check for empty input and no image preview
        if (text1 === "" && !this.userData.file.data) return;

        // Set user message and prepare to send it
        this.userData.message = text1;
        this.messages.push({ ...this.userData });

        // Send message to the server
        fetch(`${window.SCRIPT_ROOT || ''}/predict`, {
            method: 'POST',
            body: JSON.stringify({
                contents: [
                    {
                        parts: [
                            { text: this.userData.message },
                            ...(this.userData.file.data ? [{ inline_data: this.userData.file }] : [])
                        ]
                    }
                ]
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            this.botData.message = data.answer;
            this.botData.file = (data.file && data.file.data && data.file.mime_type)
                ? { data: data.file.data, mime_type: data.file.mime_type }
                : null;
            this.messages.push({ ...this.botData });
        })
        .catch(error => {
            console.error('Error:', error);
            this.messages.push({ name: "PerfectFit", message: "Sorry, I couldn't reach the server. Please try again.", file: null });
        })
        .finally(() => {
            this.updateChatText(chatBox);
            textField.value = '';
            this.resetUserData();
            this.resetbotData();
            this.clearImagePreview();
        });
    }

    updateChatText(chatBox) {
        // Build nodes with textContent so model output or product text can never inject HTML.
        const chatMessage = chatBox.querySelector('.chatbox__messages');
        chatMessage.replaceChildren();
        this.messages.slice().reverse().forEach(item => {
            const div = document.createElement('div');
            div.className = 'messages__item ' + (item.name === "PerfectFit" ? 'messages__item--visitor' : 'messages__item--operator');
            const text = document.createElement('p');
            text.textContent = item.message || '';
            div.appendChild(text);
            if (item.file && item.file.data && /^image\/(jpeg|png|webp|gif)$/.test(item.file.mime_type || '')) {
                const caption = document.createElement('p');
                caption.textContent = item.name === "PerfectFit" ? "Here is the product's image:" : '';
                const img = document.createElement('img');
                img.src = `data:${item.file.mime_type};base64,${item.file.data}`;
                img.className = 'attachment';
                img.style.cssText = 'width: 50%; margin-top: 10px; margin-bottom: 10px;';
                if (caption.textContent) div.appendChild(caption);
                div.appendChild(img);
            }
            chatMessage.appendChild(div);
        });
    }

    onFileChange(fileInput) {
        const file = fileInput.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const { fileUploadWrapper, imgPreview, fileUploadButton } = this.args;
            imgPreview.src = e.target.result;
            imgPreview.style.display = 'block'; // Show the preview in the footer
            fileUploadWrapper.classList.add("file-uploaded");
            
            // Hide the paperclip icon
            fileUploadButton.style.display = 'none';

            // Convert image to base64 string and store it in userData
            const base64String = e.target.result.split(",")[1];
            this.userData.file = {
                data: base64String,
                mime_type: file.type
            };
            fileInput.value = ""; // Clear the input for future use
        };
        reader.readAsDataURL(file);
    }

    clearImagePreview() {
        const { imgPreview, fileUploadWrapper, fileUploadButton } = this.args;
        imgPreview.src = ""; // Clear the image source
        imgPreview.style.display = "none"; // Hide the preview
        fileUploadWrapper.classList.remove("file-uploaded"); // Reset upload wrapper state

        // Show the paperclip icon again
        fileUploadButton.style.display = 'block';

        // Clear file data in userData
        this.userData.file = { data: null, mime_type: null };
    }

    resetUserData() {
        // Reset userData after each message is sent
        this.userData = {
            message: null,
            name: "User",
            file: {
                data: null,
                mime_type: null
            }
        };
    }
    resetbotData() {
        // Reset userData after each message is sent
        this.botData = {
            message: null,
            name: "PerfectFit",
            file: {
                data: null,
                mime_type: null
            }
        };
    }
}

// Initialize chatbox
const chatbox = new Chatbox();
chatbox.display();

