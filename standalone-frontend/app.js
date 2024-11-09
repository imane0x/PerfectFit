// class Chatbox {
//     constructor() {
//         this.args = {
//             openButton: document.querySelector('.chatbox__button'),
//             chatBox: document.querySelector('.chatbox__support'),
//             sendButton: document.querySelector('.send__button'),
//         }

//         this.state = false;
//         this.messages = [];
//     }

//     display() {
//         const {openButton, chatBox, sendButton} = this.args;

//         openButton.addEventListener('click', () => this.toggleState(chatBox))

//         sendButton.addEventListener('click', () => this.onSendButton(chatBox))

//         const node = chatBox.querySelector('input');
//         node.addEventListener("keyup", ({key}) => {
//             if (key === "Enter") {
//                 this.onSendButton(chatBox)
//             }

//         })
//     }

//     toggleState(chatbox) {
//         this.state = !this.state;

//         // show or hides the box
//         if(this.state) {
//             chatbox.classList.add('chatbox--active')
//         } else {
//             chatbox.classList.remove('chatbox--active')
//         }
//     }

//     onSendButton(chatbox) {
//         var textField = chatbox.querySelector('input');
//         let text1 = textField.value
//         if (text1 === "") {
//             return;
//         }

//         let msg1 = { name: "User", message: text1 }
//         this.messages.push(msg1);

//         fetch('http://127.0.0.1:5000/predict', {
//             method: 'POST',
//             body: JSON.stringify({ message: text1 }),
//             mode: 'cors',
//             headers: {
//               'Content-Type': 'application/json'
//             },
//           })
//           .then(r => r.json())
//           .then(r => {
//             let msg2 = { name: "Sam", message: r.answer };
//             this.messages.push(msg2);
//             this.updateChatText(chatbox)
//             textField.value = ''

//         }).catch((error) => {
//             console.error('Error:', error);
//             this.updateChatText(chatbox)
//             textField.value = ''
//           });
//     }

//     updateChatText(chatbox) {
//         var html = '';
//         this.messages.slice().reverse().forEach(function(item, index) {
//             if (item.name === "Sam")
//             {
//                 html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>'
//             }
//             else
//             {
//                 html += '<div class="messages__item messages__item--operator">' + item.message + '</div>'
//             }
//           });

//         const chatmessage = chatbox.querySelector('.chatbox__messages');
//         chatmessage.innerHTML = html;
//     }
// }


// const chatbox = new Chatbox();
// chatbox.display();


class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            selectImage: document.querySelector('.upload__button'),
            inputFile: document.querySelector('#uploadImage'), // file input for image
            imgArea: document.querySelector('.img__area') // image display area
        };

        this.state = false;
        this.messages = [];
        console.log("Chatbox initialized with elements:", this.args);
    }

    display() {
        const { openButton, chatBox, sendButton, selectImage, inputFile, imgArea } = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox));
        sendButton.addEventListener('click', () => this.onSendButton(chatBox));
        selectImage.addEventListener('click', function () {
            inputFile.click();
        })
        // Trigger file input click on button click
      //  selectImage.addEventListener('click', () => inputFile.click());
      selectImage.addEventListener('click', () => {
        console.log("Upload button clicked");
        inputFile.click(); // Trigger hidden input click
        });

        // Handle image file selection and preview
        inputFile.addEventListener('change', function () {
            const image = this.files[0];
            if (image && image.size < 2000000) { // Limit file size to 2MB
                const reader = new FileReader();
                reader.onload = () => {
                    imgArea.innerHTML = ''; // Clear any previous image
                    const img = document.createElement('img');
                    img.src = reader.result;
                    img.alt = 'Uploaded Image';
                    img.classList.add('uploaded-image'); // Optional class for styling
                    imgArea.appendChild(img);
                    imgArea.classList.add('active');
                    imgArea.dataset.img = image.name;
                };
                reader.readAsDataURL(image);
            } else {
                alert("Image size is more than 2MB.");
            }
        });

        const node = chatBox.querySelector('input[type="text"]');
        node.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                this.onSendButton(chatBox);
            }
        });
    }

    toggleState(chatbox) {
        this.state = !this.state;
        chatbox.classList.toggle('chatbox--active', this.state);
    }

    onSendButton(chatbox) {
        const textField = chatbox.querySelector('input[type="text"]');
        const text1 = textField.value.trim();
        if (!text1) return;

        const msg1 = { name: "User", message: text1 };
        this.messages.push(msg1);

        fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            body: JSON.stringify({ message: text1 }),
            mode: 'cors',
            headers: { 'Content-Type': 'application/json' },
        })
        .then(r => r.json())
        .then(r => {
            const msg2 = { name: "Sam", message: r.answer };
            this.messages.push(msg2);
            this.updateChatText(chatbox);
            textField.value = '';
        })
        .catch(error => {
            console.error('Error:', error);
            this.updateChatText(chatbox);
            textField.value = '';
        });
    }

    updateChatText(chatbox) {
        let html = '';
        this.messages.slice().reverse().forEach(item => {
            html += item.name === "Sam"
                ? `<div class="messages__item messages__item--visitor">${item.message}</div>`
                : `<div class="messages__item messages__item--operator">${item.message}</div>`;
        });
        chatbox.querySelector('.chatbox__messages').innerHTML = html;
    }
}

const chatbox = new Chatbox();
chatbox.display();
