// --- Global State Management ---
let cartItemCount = parseInt(sessionStorage.getItem('vibeHiveCartCount')) || 0;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    updateCartBadge();
    
    // Set up event listener for the chatbot input (Ensures Enter key works)
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


// --- Placeholder E-commerce/Admin/Other Functions ---
// (These functions would be needed on other pages, included here for completeness if index.js is used globally)

function addToCart(quantity = 1) {
    cartItemCount += quantity;
    sessionStorage.setItem('vibeHiveCartCount', cartItemCount);
    
    showToast(`${quantity} item(s) added to cart!`, "success");
    updateCartBadge(); 
    
    // Animation
    const cartIcon = document.getElementById('cart-icon');
    if (cartIcon) {
        cartIcon.style.transform = 'scale(1.2)';
        setTimeout(() => { cartIcon.style.transform = 'scale(1.0)'; }, 300);
    }
}

function changeQuantity(change) {
    // This function is for the product detail page, included for completeness
    const quantityInput = document.getElementById('quantity');
    if (!quantityInput) return;
    let currentQuantity = parseInt(quantityInput.value);
    let newQuantity = currentQuantity + change;

    if (newQuantity >= 1) {
        quantityInput.value = newQuantity;
    }
}

// Add other simulation functions (simulateLogin, simulateRegister, loadDashboardSection, etc.) here if needed.

