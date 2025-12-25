// --- Global State Management ---
let cartItemCount = parseInt(sessionStorage.getItem('vibeHiveCartCount')) || 0;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', function () {
    updateCartBadge();
    // fetchProducts();
    applyFiltersFromURL();
    loadCategoryCounts();
    syncCartBadgeFromServer();

    const chatbotInput = document.getElementById('chatbot-input');
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') simulateChatResponse();
        });
    }
});

// --- Fetch Products from Flask ---

function fetchProducts() {
    fetch('http://127.0.0.1:5000/products')
        .then(response => response.json())
        .then(products => {
            const productGrid = document.getElementById('product-grid');
            productGrid.innerHTML = '';

            if (!products.length) {
                productGrid.innerHTML = `<div class="col-12 text-center text-muted">No products available yet.</div>`;
                return;
            }

            products.forEach(prod => {
                const imageUrl = prod.image_path
                    ? `http://127.0.0.1:5000/uploads/${prod.image_path}`
                    : 'assets/images/default-product.jpg';

                const categoryText = `${prod.main_category} → ${prod.sub_category}`;

                const availability = prod.stock_quantity > 0
                    ? `<span class="text-success font-weight-bold">Available</span>`
                    : `<span class="text-danger font-weight-bold">Unavailable</span>`;

                const productCard = `
        <div class="col-md-4 col-sm-6 mb-4 product-item" data-category="${prod.main_category}">
            <div class="product-card">
                <a href="product-detail.html?product_id=${prod.product_id}" style="text-decoration: none; color: inherit;">
                    <div class="category-img-container">
                        <img src="${imageUrl}" alt="${prod.product_name}" class="img-fluid">
                    </div>
                    <h5 class="text-primary">${prod.product_name}</h5>
                    <p class="text-muted small">${categoryText}</p>

                    <p class="h4 text-highlight mb-1">Rs.${parseFloat(prod.price).toFixed(2)}</p>

                    <p class="mb-2">${availability}</p>
                </a>

                <button class="btn btn-primary-vibe btn-sm"
        onclick="window.location.href='product-detail.html?product_id=${prod.product_id}'">
    View Detail
</button>

            </div>
        </div>
    `;

                productGrid.insertAdjacentHTML('beforeend', productCard);
            });

        })
        .catch(err => {
            console.error('Error fetching products:', err);
            showToast('Failed to load products.', 'error');
        });
}


// --- Add to Cart (requires logged-in customer) ---
async function addToCart(productId, quantity = 1) {
    const customer = JSON.parse(localStorage.getItem('loggedInCustomer'));

    if (!customer) {
        showToast("Please log in to add items to cart.", "error");
        setTimeout(() => { window.location.href = "login.html"; }, 900);
        return;
    }

    console.log("🛒 Adding to cart:", customer.id, productId, quantity);

    try {
        const res = await fetch('http://127.0.0.1:5000/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_id: customer.id,
                product_id: productId,
                quantity: quantity
            })
        });

        const data = await res.json();
        if (res.ok) {
            showToast(data.message || "Added to cart!", "success");

            let cartCount = parseInt(sessionStorage.getItem('vibeHiveCartCount') || '0');
            cartCount += quantity;
            sessionStorage.setItem('vibeHiveCartCount', cartCount);
            cartItemCount = cartCount;
            updateCartBadge();
        } else {
            showToast(data.message || "Failed to add item.", "error");
        }
    } catch (err) {
        console.error("Error adding to cart:", err);
        showToast("Server connection error.", "error");
    }
}

// --- Utility Functions ---
function updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    if (!badge) return;

    if (cartItemCount > 0) {
        badge.textContent = cartItemCount;
        badge.style.display = 'block';
    } else {
        badge.style.display = 'none';
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast-notification');
    if (!toast) return;

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
    setTimeout(() => { toast.classList.add('d-none'); }, 3000);
}

// --- Chatbot ---
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



// --- Filters ---
function simulateFilter(type, value, event) {
    if (event) event.preventDefault();

    let category = null;
    let subcategory = null;
    let sort = null;

    document.querySelectorAll('.filter-link')
        .forEach(link => link.classList.remove('font-weight-bold'));

    if (event && type !== 'reset')
        event.target.classList.add('font-weight-bold');

    if (type === 'reset') {
        fetchProducts();
        showToast("Filters reset.", "success");
        return;
    }

    if (type === 'category') category = value;
    if (type === 'subcategory') subcategory = value;
    if (type === 'price') sort = value;

    fetchFilteredProducts(category, subcategory, sort);
}



function fetchFilteredProducts(category = null, subcategory = null, sort = null) {
    let url = 'http://127.0.0.1:5000/products';
    const params = [];

    if (category) params.push(`category=${encodeURIComponent(category)}`);
    if (subcategory) params.push(`subcategory=${encodeURIComponent(subcategory)}`);
    if (sort) params.push(`sort=${encodeURIComponent(sort)}`);

    if (params.length > 0) url += '?' + params.join('&');

    fetch(url)
        .then(res => res.json())
        .then(products => {
            const productGrid = document.getElementById('product-grid');
            productGrid.innerHTML = '';

            if (!products.length) {
                productGrid.innerHTML =
                    `<div class="col-12 text-center text-muted">No products found.</div>`;
                return;
            }

            products.forEach(prod => {
                const imageUrl = prod.image_path
                    ? `http://127.0.0.1:5000/uploads/${prod.image_path}`
                    : 'assets/images/default-product.jpg';

                const availability = prod.stock_quantity > 0
                    ? `<span class="text-success font-weight-bold">Available</span>`
                    : `<span class="text-danger font-weight-bold">Unavailable</span>`;

                const disableBtn = prod.stock_quantity > 0 ? "" : "disabled";

                productGrid.innerHTML += `
        <div class="col-md-4 col-sm-6 mb-4 product-item">
            <div class="product-card">

                <a href="product-detail.html?product_id=${prod.product_id}" style="text-decoration: none; color: inherit;">
                    <div class="category-img-container">
                        <img src="${imageUrl}" class="img-fluid">
                    </div>

                    <h5 class="text-primary">${prod.product_name}</h5>
                    <p class="text-muted small">${prod.main_category} → ${prod.sub_category}</p>

                    <p class="h4 text-highlight mb-1">
                        Rs.${parseFloat(prod.price).toFixed(2)}
                    </p>

                    <!-- 🔥 Availability added here -->
                    <p class="mb-2">${availability}</p>
                </a>

                <button class="btn btn-primary-vibe btn-sm" ${disableBtn}
                    onclick="window.location.href='product-detail.html?product_id=${prod.product_id}'">
                    View Detail
                </button>

            </div>
        </div>`;
            });

        })
        .catch(() => showToast("Failed to apply filters.", "error"));
}



// --- Category Sidebar ---

function loadCategoryCounts() {
    fetch('http://127.0.0.1:5000/categories')
        .then(response => response.json())
        .then(categories => {
            const categoryList = document.getElementById('category-list');
            categoryList.innerHTML = '';

            categories.forEach(cat => {
                // MAIN CATEGORY
                categoryList.innerHTML += `
                <li class="mt-2">
                    <a href="#" class="filter-link font-weight-bold"
                       onclick="simulateFilter('category', '${cat.main_category}', event)">
                       ${cat.main_category} (${cat.total})
                    </a>
                </li>`;

                // SUB-CATEGORIES (Fix: include main category + subcategory)
                if (cat.subcategories && cat.subcategories.length > 0) {
                    cat.subcategories.forEach(sub => {
                        categoryList.innerHTML += `
                        <li class="ml-3">
                            <a href="#" class="filter-link small"
                               onclick="simulateFilterSubcategory('${cat.main_category}', '${sub.name}', event)">
                               ↳ ${sub.name} (${sub.count})
                            </a>
                        </li>`;
                    });
                }
            });
        });
}



// --- Sync Cart Count from Server ---
async function syncCartBadgeFromServer() {
    const customer = JSON.parse(localStorage.getItem('loggedInCustomer'));
    if (!customer) return;
    try {
        const res = await fetch(`http://127.0.0.1:5000/cart/summary?customer_id=${encodeURIComponent(customer.id)}`);
        if (!res.ok) return;
        const data = await res.json();
        const count = data.total_items || 0;
        sessionStorage.setItem('vibeHiveCartCount', count);
        cartItemCount = parseInt(count);
        updateCartBadge();
    } catch (err) {
        console.warn('Could not sync cart count:', err);
    }
}
function simulateFilterSubcategory(category, subcategory, event) {
    if (event) event.preventDefault();

    // bold highlight
    document.querySelectorAll('.filter-link')
        .forEach(link => link.classList.remove('font-weight-bold'));

    event.target.classList.add('font-weight-bold');

    // fetch with BOTH filters
    window.location.href =
        `product.html?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}`;
}




