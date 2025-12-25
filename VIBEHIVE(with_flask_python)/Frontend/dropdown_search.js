console.log("🚀 Search script loaded");
// this code is for nav bar categories show on product drop down
function loadNavbarCategories() {
    fetch('http://127.0.0.1:5000/categories')
        .then(res => res.json())
        .then(categories => {
            const container = document.getElementById('navbar-category-list');
            container.innerHTML = '';

            categories.forEach(cat => {
                // Main category
                container.innerHTML += `
                    <a class="dropdown-item font-weight-bold"
                       href="product.html?category=${encodeURIComponent(cat.main_category)}">
                       ${cat.main_category} (${cat.total})
                    </a>
                `;

                // Subcategories
                if (cat.subcategories) {
                    cat.subcategories.forEach(sub => {
                        container.innerHTML += `
                            <a class="dropdown-item pl-4 small"
                               href="product.html?category=${encodeURIComponent(cat.main_category)}&subcategory=${encodeURIComponent(sub.name)}">
                               ↳ ${sub.name} (${sub.count})
                            </a>
                        `;
                    });
                }

                container.innerHTML += `<div class="dropdown-divider"></div>`;
            });
        })
        .catch(() => {
            document.getElementById('navbar-category-list').innerHTML =
                `<span class="text-danger small">Failed to load categories</span>`;
        });
}

// Load once when page loads
document.addEventListener('DOMContentLoaded', loadNavbarCategories);

document.addEventListener('DOMContentLoaded', applyFiltersFromURL);




function applyFiltersFromURL() {
    const params = new URLSearchParams(window.location.search);

    const category = params.get('category');
    const subcategory = params.get('subcategory');

    if (category && subcategory) {
        fetchFilteredProducts(category, subcategory);
    } else if (category) {
        fetchFilteredProducts(category);
    } else {
        fetchProducts();
    }
}




// //search code


document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("productSearch");
    const resultsDiv = document.getElementById("searchResults");
    let timer;

    if (!input || !resultsDiv) {
        console.error("❌ Search input or results div not found");
        return;
    }

    // ✅ ensure hidden on load
    resultsDiv.style.display = "none";

    input.addEventListener("input", () => {
        clearTimeout(timer);

        const query = input.value.trim();

        // ✅ hide when input is empty or too short
        if (query.length < 2) {
            resultsDiv.innerHTML = "";
            resultsDiv.style.display = "none";
            return;
        }

        timer = setTimeout(async () => {
            try {
                const res = await fetch(
                    `http://127.0.0.1:5000/search?q=${encodeURIComponent(query)}`
                );
                const products = await res.json();

                // ✅ show box only when results exist
                if (!products.length) {
                    resultsDiv.innerHTML = "<small>No results found</small>";
                    resultsDiv.style.display = "block";
                    return;
                }

                resultsDiv.innerHTML = products.map(p => `
                    <a href="product-detail.html?product_id=${p.product_id}"
                       class="search-item d-flex align-items-center mb-2 text-dark text-decoration-none">
                        <img src="http://127.0.0.1:5000/uploads/${p.image_path}" width="40" class="mr-2">
                        <div>
                            <strong>${p.product_name}</strong><br>
                            Rs.${p.price}<br>
                            ${p.stock_quantity > 0
                                ? '<small style="color:green">In Stock</small>'
                                : '<small style="color:red">Out of Stock</small>'}
                        </div>
                    </a>
                `).join("");

                resultsDiv.style.display = "block";
            } catch (err) {
                console.error("Search error:", err);
                resultsDiv.style.display = "none";
            }
        }, 300);
    });

    // ✅ hide when clicking outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest("#productSearch") &&
            !e.target.closest("#searchResults")) {
            resultsDiv.style.display = "none";
        }
    });
});
