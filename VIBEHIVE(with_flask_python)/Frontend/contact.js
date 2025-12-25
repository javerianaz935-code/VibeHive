// --- Global State Management ---
let cartItemCount = parseInt(sessionStorage.getItem('vibeHiveCartCount')) || 0;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    updateCartBadge();
    
    // Set up event listener for the chatbot input
    const chatbotInput = document.getElementById('chatbot-input');
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                simulateChatResponse();
            }
        });
    }
});

// --- Utility Functions ---

function updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    if (badge) { 
        if (cartItemCount > 0) {
            badge.textContent = cartItemCount;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast-notification');
    if (!toast) return; // Add a check to ensure toast element exists

    const toastText = toast.querySelector('span');
    const toastIcon = toast.querySelector('i');
    
    const rootStyles = getComputedStyle(document.documentElement);
    const colorAccent = rootStyles.getPropertyValue('--color-accent').trim();

    toastText.textContent = message;
    
    toast.style.borderColor = '';
    toastIcon.classList.remove('fa-exclamation-triangle', 'fa-check-circle');

    if (type === 'error') {
        toast.style.borderColor = 'red';
        toastIcon.classList.add('fa-exclamation-triangle');
    } else {
        toast.style.borderColor = colorAccent;
        toastIcon.classList.add('fa-check-circle');
    }

    toast.classList.remove('d-none');
    setTimeout(() => {
        toast.classList.add('d-none');
    }, 3000);
}


// --- CORE CHATBOT FUNCTIONS (Final, Corrected Logic) ---

function toggleChatbot() {
    const modal = document.getElementById('chatbot-modal');
    // FIXED: Uses explicit style check for reliable toggling
    if (modal) {
        modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
    }
}

function simulateChatResponse() {
    const input = document.getElementById('chatbot-input');
    const body = document.querySelector('.chatbot-body');
    const userMessage = input.value.trim();

    if (userMessage === '') return;

    const colorPrimary = getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim();

    // Display user message
    body.innerHTML += `<div class="text-right mb-2" style="color: ${colorPrimary}">You: ${userMessage}</div>`;

    // Simulate AI response (SDD 1.6.7)
    const botResponse = "Query acknowledged. I am ready for general support questions or guiding you through the site!";

    setTimeout(() => {
        body.innerHTML += `<div class="text-left mb-2 text-muted">Bot: ${botResponse}</div>`;
        body.scrollTop = body.scrollHeight; 
    }, 500);

    input.value = '';
    body.scrollTop = body.scrollHeight;
}


// --- Contact Form Integration with Flask Backend ---
document.addEventListener("DOMContentLoaded", () => {
    const contactForm = document.getElementById("contact-form");
    if (!contactForm) return;

    contactForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const name = document.getElementById("contact-name").value.trim();
        const email = document.getElementById("contact-email").value.trim();
        const subject = document.getElementById("contact-subject").value.trim();
        const message = document.getElementById("contact-message").value.trim();

        if (!name || !email || !subject || !message) {
            showToast("Please fill in all fields correctly.", "error");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:5000/contact", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name,
                    email,
                    message: `${subject}\n\n${message}`
                }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showToast("Message sent successfully!", "success");
                contactForm.reset();
            } else {
                showToast(data.error || "Failed to send message.", "error");
            }
        } catch (error) {
            console.error("❌ Contact form error:", error);
            showToast("Server error. Please try again later.", "error");
        }
    });
});


// Add other necessary global functions if needed for other linked pages,
// but keep this specific JS file focused on contact.html if preferred.

fetch("http://127.0.0.1:5000/contact", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: document.getElementById("name").value,
    email: document.getElementById("email").value,
    message: document.getElementById("message").value
  })
})
.then(res => res.json())
.then(data => alert(data.message || data.error));
