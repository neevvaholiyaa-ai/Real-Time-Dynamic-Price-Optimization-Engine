/**
 * Real-Time Dynamic Pricing Dashboard — Client Script
 * Handles asynchronous communication with backend pricing microservice,
 * scenario presets loading, and interactive recommendation rendering.
 */

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("pricingForm");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnLoader = submitBtn.querySelector(".btn-loader");
    const presetSelect = document.getElementById("presetSelect");

    const resultPlaceholder = document.getElementById("resultPlaceholder");
    const resultContent = document.getElementById("resultContent");

    const resCurrentPrice = document.getElementById("resCurrentPrice");
    const resRecommendedPrice = document.getElementById("resRecommendedPrice");
    const resPriceDiff = document.getElementById("resPriceDiff");
    const resPriceDiffPct = document.getElementById("resPriceDiffPct");
    const resActionBadge = document.getElementById("resActionBadge");
    const resMinPrice = document.getElementById("resMinPrice");
    const resMaxPrice = document.getElementById("resMaxPrice");
    const rangePin = document.getElementById("rangePin");
    const resInsightsList = document.getElementById("resInsightsList");

    let sampleScenarios = [];

    // Helper: Currency Formatter
    const formatINR = (val) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 2
        }).format(val);
    };

    // Resolve backend API URL (supports local integrated serving, standalone Vercel frontend, and Render backend)
    const API_BASE_URL = window.API_BASE_URL || "";

    // 1. Fetch Demo Scenarios from Backend
    async function loadPresets() {
        try {
            const resp = await fetch(`${API_BASE_URL}/api/catalog-samples`);
            if (resp.ok) {
                sampleScenarios = await resp.json();
                sampleScenarios.forEach((item, idx) => {
                    const opt = document.createElement("option");
                    opt.value = idx;
                    opt.textContent = item.label;
                    presetSelect.appendChild(opt);
                });
            }
        } catch (err) {
            console.warn("Could not load presets:", err);
        }
    }

    // 2. Populate Form when Preset Chosen
    presetSelect.addEventListener("change", (e) => {
        const idx = e.target.value;
        if (idx === "" || !sampleScenarios[idx]) return;
        const s = sampleScenarios[idx];

        document.getElementById("productName").value = s.product_name;
        document.getElementById("categorySelect").value = s.category;
        document.getElementById("citySelect").value = s.city;
        document.getElementById("costPrice").value = s.cost_price;
        document.getElementById("currentPrice").value = s.current_price;
        document.getElementById("mrp").value = s.mrp;
        document.getElementById("competitorPrice").value = s.competitor_avg_price;
        document.getElementById("stockLevel").value = s.stock_level;
        document.getElementById("dailyOrders").value = s.orders;
        document.getElementById("daysToFestival").value = s.days_until_next_festival;
        document.getElementById("weatherType").value = s.weather_type;

        // Auto trigger recommendation calculation
        submitForm();
    });

    // 3. Handle Form Submission
    async function submitForm() {
        // Collect form data
        const payload = {
            product_name: document.getElementById("productName").value,
            category: document.getElementById("categorySelect").value,
            city: document.getElementById("citySelect").value,
            cost_price: parseFloat(document.getElementById("costPrice").value),
            current_price: parseFloat(document.getElementById("currentPrice").value),
            mrp: parseFloat(document.getElementById("mrp").value),
            competitor_avg_price: parseFloat(document.getElementById("competitorPrice").value),
            stock_level: parseInt(document.getElementById("stockLevel").value),
            orders: parseInt(document.getElementById("dailyOrders").value),
            days_until_next_festival: parseInt(document.getElementById("daysToFestival").value),
            weather_type: document.getElementById("weatherType").value,
            competitor_stock_status: "In_Stock"
        };

        // Basic Client Validation
        if (payload.cost_price > payload.mrp) {
            alert("Cost Price cannot exceed Maximum Retail Price (MRP).");
            return;
        }

        // Set Loading State
        submitBtn.disabled = true;
        btnText.style.display = "none";
        btnLoader.style.display = "flex";

        try {
            const resp = await fetch(`${API_BASE_URL}/predict`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) {
                const errData = await resp.json();
                throw new Error(errData.detail || "Pricing optimization request failed.");
            }

            const data = await resp.json();
            renderResult(data);
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            submitBtn.disabled = false;
            btnText.style.display = "block";
            btnLoader.style.display = "none";
        }
    }

    // 4. Render Recommendation Results
    function renderResult(data) {
        resultPlaceholder.style.display = "none";
        resultContent.style.display = "flex";

        // Main Prices
        resCurrentPrice.textContent = formatINR(data.current_price);
        resRecommendedPrice.textContent = formatINR(data.recommended_price);

        // Price Diff & %
        const diffSign = data.price_change >= 0 ? "+" : "";
        resPriceDiff.textContent = `${diffSign}${formatINR(data.price_change)}`;
        resPriceDiffPct.textContent = `${diffSign}${data.price_change_percentage.toFixed(1)}%`;

        // Color difference text
        if (data.price_change > 0) {
            resPriceDiff.style.color = "var(--accent-emerald)";
            resPriceDiffPct.style.color = "var(--accent-emerald)";
        } else if (data.price_change < 0) {
            resPriceDiff.style.color = "#60a5fa";
            resPriceDiffPct.style.color = "#60a5fa";
        } else {
            resPriceDiff.style.color = "var(--accent-amber)";
            resPriceDiffPct.style.color = "var(--accent-amber)";
        }

        // Recommendation Badge
        resActionBadge.textContent = data.recommendation;
        resActionBadge.className = "badge";
        if (data.recommendation === "Increase Price") {
            resActionBadge.classList.add("increase");
        } else if (data.recommendation === "Decrease Price") {
            resActionBadge.classList.add("decrease");
        } else {
            resActionBadge.classList.add("hold");
        }

        // Guardrail Limits & Range Pin calculation
        resMinPrice.textContent = `Min Floor: ${formatINR(data.min_allowed_price)}`;
        resMaxPrice.textContent = `Max Ceiling: ${formatINR(data.max_allowed_price)}`;

        const min = data.min_allowed_price;
        const max = data.max_allowed_price;
        const rec = data.recommended_price;
        let pct = 50;
        if (max > min) {
            pct = Math.max(5, Math.min(95, ((rec - min) / (max - min)) * 100));
        }
        rangePin.style.left = `${pct}%`;

        // Render Insights
        resInsightsList.innerHTML = "";
        data.insights.forEach(insight => {
            const li = document.createElement("li");
            li.textContent = insight;
            resInsightsList.appendChild(li);
        });

        // Smooth scroll on mobile
        if (window.innerWidth < 960) {
            resultContent.scrollIntoView({ behavior: 'smooth' });
        }
    }

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        submitForm();
    });

    // Initialize presets
    loadPresets();
});
