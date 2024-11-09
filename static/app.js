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
        fetch('http://127.0.0.1:5000/predict', {
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
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            // // Set bot message and update chat
             this.botData.message = data.answer;
     
            if (data.file && data.file.data && data.file.mime_type) {
                this.botData.file.data = data.file.data.split(",")[1];
                this.botData.file.mime_type = data.file.mime_type;
          



            } else {
                // Handle the case when file_info is not present or incomplete
                this.botData.file = null;
                this.botData.mime_type = null;
            }

            console.log(this.botData)
            this.messages.push({ ...this.botData});
            this.updateChatText(chatBox);
            textField.value = ''; // Clear the input field
            this.resetUserData(); // Reset user data after sending
            this.resetbotData();
            this.clearImagePreview(); // Remove the preview image
        })
        .catch(error => {
            console.error('Error:', error);
            this.updateChatText(chatBox);
            textField.value = '';
            this.resetUserData();
            this.clearImagePreview();
        });
    }



updateChatText(chatBox) {
    const chatMessage = chatBox.querySelector('.chatbox__messages');
    chatMessage.innerHTML = this.messages.slice().reverse().map(item => {
        const messageClass = item.name === "PerfectFit" ? 'messages__item--visitor' : 'messages__item--operator';
        const textBeforeImage = "<p> Here is the product's image:</p>"; 

        return `
            <div class="messages__item ${messageClass}">
                ${item.message}
                ${item.file && item.file.data ? `
                    ${textBeforeImage} 
                    <img src="data:${item.file.mime_type};base64,${item.file.data}" class="attachment" style="width: 50%" margin-top: 10px; margin-bottom: 10px;" />` : ''}
            </div>
        `;
    }).join('');
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

