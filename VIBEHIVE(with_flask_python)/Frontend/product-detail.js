// ------------------------
// PRODUCT DETAIL PAGE
// ------------------------

document.addEventListener("DOMContentLoaded", () => {
    loadProductDetail();
    updateCartBadge();
});

// ------------------------
// Extract product_id from URL
// ------------------------
function getProductId() {
    const params = new URLSearchParams(window.location.search);
    return params.get("product_id") || params.get("id");
}

// ------------------------
// Fetch Product Details
// ------------------------
function loadProductDetail() {
    const productId = getProductId();
    if (!productId) {
        console.error("❌ product_id missing in URL");
        document.getElementById("product-detail-container").innerHTML =
            `<p class="text-danger text-center">Invalid Product Request</p>`;
        return;
    }

    fetch(`http://127.0.0.1:5000/product/${productId}`)
        .then(res => res.json())
        .then(product => {
            if (!product || product.error) {
                document.getElementById("product-detail-container").innerHTML =
                    `<p class="text-danger text-center">Product not found.</p>`;
                return;
            }

            renderProductDetail(product);
        })
        .catch(err => {
            console.error("Error fetching product:", err);
            document.getElementById("product-detail-container").innerHTML =
                `<p class="text-danger text-center">Server error loading product.</p>`;
        });
}

// ------------------------
// Render detailed view
// ------------------------
// function renderProductDetail(prod) {

//     const imageUrl = prod.image_path
//         ? `http://127.0.0.1:5000/uploads/${prod.image_path}`
//         : "assets/images/default-product.jpg";

//     document.getElementById("detail-image").src = imageUrl;

//     document.getElementById("detail-name").textContent = prod.product_name;
//     document.getElementById("detail-category").textContent =
//         `${prod.main_category} → ${prod.sub_category}`;

//     document.getElementById("detail-price").textContent =
//         parseFloat(prod.price).toFixed(2);

//     document.getElementById("detail-description").textContent =
//         prod.description || "No description available.";

//     // Button
//     const btn = document.getElementById("add-to-cart-btn");
//     btn.disabled = prod.stock_quantity <= 0;
//     btn.setAttribute("onclick", `addToCart(${prod.product_id}, 1)`);

// }

function renderProductDetail(prod) {

    const imageUrl = prod.image_path
        ? `http://127.0.0.1:5000/uploads/${prod.image_path}`
        : "assets/images/default.jpg";

    document.getElementById("detail-image").src = imageUrl;
    document.getElementById("detail-name").textContent = prod.product_name;

    document.getElementById("detail-category").textContent =
        `${prod.main_category} → ${prod.sub_category}`;

    document.getElementById("detail-price").textContent =
        parseFloat(prod.price).toFixed(2);

    document.getElementById("detail-description").textContent =
        prod.description || "No description available.";

    // --------------------------------
    // 🔥 STOCK AVAILABILITY TEXT
    // --------------------------------
    const availabilityBox = document.getElementById("detail-availability");

    if (prod.stock_quantity > 0) {
        availabilityBox.innerHTML =
            `<span class="text-success">Available</span>`;
    } else {
        availabilityBox.innerHTML =
            `<span class="text-danger">Unavailable</span>`;
    }

    // --------------------------------
    // 🔥 ADD TO CART BUTTON HANDLING
    // --------------------------------
    const btn = document.getElementById("add-to-cart-btn");

    if (prod.stock_quantity > 0) {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-cart-plus"></i> Add to Cart`;
        btn.classList.remove("btn-secondary");
        btn.classList.add("btn-primary-vibe");

        btn.onclick = function () {
            addToCart(prod.product_id,
                      parseInt(document.getElementById("detail-quantity").value));
        };

    } else {
        btn.disabled = true;
        btn.innerHTML = `Out of Stock`;
        btn.classList.remove("btn-primary-vibe");
        btn.classList.add("btn-secondary");
        btn.onclick = null;
    }
}

// ------------------------
// CART BADGE (Same as product.js)
// ------------------------
let cartItemCount = parseInt(sessionStorage.getItem("vibeHiveCartCount")) || 0;

function updateCartBadge() {
    const badge = document.getElementById("cart-badge");
    if (!badge) return;

    if (cartItemCount > 0) {
        badge.textContent = cartItemCount;
        badge.style.display = "block";
    } else {
        badge.style.display = "none";
    }
}

// ------------------------
// ADD TO CART (Reuse from product.js)
// ------------------------
async function addToCart(productId, quantity = 1) {
    const customer = JSON.parse(localStorage.getItem("loggedInCustomer"));

    if (!customer) {
        window.location.href = "login.html";
        return;
    }

    try {
        const res = await fetch("http://127.0.0.1:5000/cart/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                customer_id: customer.id,
                product_id: productId,
                quantity: quantity
            })
        });

        const data = await res.json();

        if (res.ok) {
            let cartCount = parseInt(sessionStorage.getItem("vibeHiveCartCount") || "0");
            cartCount += quantity;
            sessionStorage.setItem("vibeHiveCartCount", cartCount);
            cartItemCount = cartCount;

            updateCartBadge();
            showToast("success", "Item added to cart!");
        } else {
            showToast("danger", data.message || "Failed to add item.");
        }
    } catch (err) {
        console.error("Error:", err);
        showToast("danger", "Server error.");
    }
}

function showToast(type, message) {
    const toast = document.getElementById("toast-notification");
    const icon = toast.querySelector(".fas");
    const text = toast.querySelector("span");

    // Apply styles
    toast.classList.remove("d-none", "alert-success", "alert-danger");
    toast.classList.add(`alert-${type}`);

    if (type === "success") {
        icon.className = "fas fa-check-circle";
    } else {
        icon.className = "fas fa-exclamation-circle";
    }

    text.textContent = message;

    // Auto-hide toast after 3 seconds
    setTimeout(() => {
        toast.classList.add("d-none");
    }, 3000);
}



function submitPriceAlert() {
    const productId = getProductId();
    const email = document.getElementById("alert-email").value.trim();
    const demandPrice = document.getElementById("alert-demand-price").value.trim();

    if (!email || !demandPrice) {
        showToast("danger", "Please enter email and desired price.");
        return;
    }

    fetch("http://127.0.0.1:5000/price-alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            product_id: productId,
            email: email,
            demand_price: parseFloat(demandPrice)
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast("success", "You will be notified when price drops!");
        } else {
            showToast("danger", data.message || "Failed to save alert.");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("danger", "Server error.");
    });
}

function toggleChatbot() {
    const modal = document.getElementById('chatbot-modal');
    if (modal) modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
}

async function simulateChatResponse() {
    const input = document.getElementById('chatbot-input');
    const userMessage = input.value.trim();
    if (!userMessage) return;

    const chatbotBody = document.querySelector('.chatbot-body');

    // --- User message ---
    const userDiv = document.createElement('div');
    userDiv.classList.add('user-message');
    userDiv.textContent = userMessage;
    chatbotBody.appendChild(userDiv);

    input.value = "";

    // --- Bot typing indicator ---
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('bot-message');
    loadingDiv.textContent = "Typing...";
    chatbotBody.appendChild(loadingDiv);
    chatbotBody.scrollTop = chatbotBody.scrollHeight;

    try {
        // ✅ Send message to Flask (with or without customer_id)
        const loggedInCustomer = JSON.parse(localStorage.getItem("loggedInCustomer"));
        const customerId = loggedInCustomer ? loggedInCustomer.id : null;

        const response = await fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: userMessage,
                customer_id: customerId
            })
        });

        const data = await response.json();

        // --- Replace loading text with chatbot reply ---
        loadingDiv.innerHTML = data.reply;  // ✅ innerHTML to render links properly
    } catch (error) {
        loadingDiv.textContent = "⚠️ Sorry, I couldn’t connect to the server.";
        console.error("Chatbot error:", error);
    }

    chatbotBody.scrollTop = chatbotBody.scrollHeight;
}



async function sendMessageToChatbot(message) {
  const loggedInCustomer = JSON.parse(localStorage.getItem("loggedInCustomer"));
const customerId = loggedInCustomer ? loggedInCustomer.id : null;

const response = await fetch("http://127.0.0.1:5000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userMessage, customer_id: customerId })
});
}




document.addEventListener("DOMContentLoaded", () => {

    const wishlistBtn = document.getElementById("wishlist-btn");
    const loggedInCustomer = JSON.parse(localStorage.getItem("loggedInCustomer"));

    const params = new URLSearchParams(window.location.search);
    const productId = params.get("product_id") || params.get("id");

    if (!wishlistBtn || !productId) return;

    // ❤️ ADD TO WISHLIST
    wishlistBtn.addEventListener("click", () => {

        if (!loggedInCustomer) {
            showToast("danger", "Please login to add items to wishlist");
            setTimeout(() => window.location.href = "login.html", 1500);
            return;
        }

        fetch("http://127.0.0.1:5000/wishlist/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                customer_id: loggedInCustomer.id,   // ✅ FIX
                product_id: productId
            })
        })
        .then(res => res.json())
        .then(() => {
            wishlistBtn.innerHTML = `<i class="fas fa-heart"></i> In Wishlist`;
            wishlistBtn.classList.remove("btn-outline-danger");
            wishlistBtn.classList.add("btn-danger");
            showToast("success", "Added to wishlist ❤️");
        })
        .catch(err => {
            console.error(err);
            showToast("danger", "Failed to add to wishlist");
        });
    });

    // 🔍 CHECK IF ALREADY IN WISHLIST
    if (loggedInCustomer) {
        fetch(`http://127.0.0.1:5000/wishlist/check?customer_id=${loggedInCustomer.id}&product_id=${productId}`)
            .then(res => res.json())
            .then(data => {
                if (data.exists) {
                    wishlistBtn.innerHTML = `<i class="fas fa-heart"></i> In Wishlist`;
                    wishlistBtn.classList.remove("btn-outline-danger");
                    wishlistBtn.classList.add("btn-danger");
                }
            });
    }
});

