/**
 * Dynamic Pricing — Retail Revenue & Margin Optimizer
 * Client Application Script
 * Manages state transitions, ambient canvas animation, presets loading,
 * input validation, live API communication, and interactive results rendering.
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------------------
    // 1. DOM Elements
    // -------------------------------------------------------------------------
    const form = document.getElementById("pricingForm");
    const submitBtn = document.getElementById("submitBtn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnLoader = submitBtn.querySelector(".btn-loader");
    const presetSelect = document.getElementById("presetSelect");

    const errorBanner = document.getElementById("errorBanner");
    const errorMessage = document.getElementById("errorMessage");
    const dismissErrorBtn = document.getElementById("dismissErrorBtn");

    const resultPlaceholder = document.getElementById("resultPlaceholder");
    const resultContent = document.getElementById("resultContent");

    const resProductSubtitle = document.getElementById("resProductSubtitle");
    const resActionBadge = document.getElementById("resActionBadge");
    const badgeIcon = document.getElementById("badgeIcon");
    const badgeText = document.getElementById("badgeText");

    const resCurrentPrice = document.getElementById("resCurrentPrice");
    const resRecommendedPrice = document.getElementById("resRecommendedPrice");
    const resPriceDiff = document.getElementById("resPriceDiff");
    const resPriceDiffPct = document.getElementById("resPriceDiffPct");
    const resActionSummary = document.getElementById("resActionSummary");

    const resMinPrice = document.getElementById("resMinPrice");
    const resCompPrice = document.getElementById("resCompPrice");
    const resMaxPrice = document.getElementById("resMaxPrice");
    const guardrailPin = document.getElementById("guardrailPin");
    const pinTooltip = document.getElementById("pinTooltip");

    const resInsightsList = document.getElementById("resInsightsList");
    const resInventoryRunway = document.getElementById("resInventoryRunway");
    const resInventoryStatusBadge = document.getElementById("resInventoryStatusBadge");
    const resInventoryStatusText = document.getElementById("resInventoryStatusText");

    // Dynamic API Base URL resolution (Configurable for Vercel/Render)
    const API_BASE_URL = window.API_BASE_URL || "";
    let sampleScenarios = [];

    // -------------------------------------------------------------------------
    // 2. Ambient Market Wave Canvas Animation (Signature Visual Element)
    // -------------------------------------------------------------------------
    const canvas = document.getElementById("marketWaveCanvas");
    if (canvas) {
        const ctx = canvas.getContext("2d");
        let width = (canvas.width = window.innerWidth);
        let height = (canvas.height = window.innerHeight);

        window.addEventListener("resize", () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        });

        const particles = Array.from({ length: 28 }, () => ({
            x: Math.random() * width,
            y: Math.random() * height,
            radius: Math.random() * 2 + 1,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            alpha: Math.random() * 0.4 + 0.1
        }));

        let step = 0;
        function animateCanvas() {
            ctx.clearRect(0, 0, width, height);
            step += 0.008;

            // Draw subtle flowing market curve
            ctx.beginPath();
            ctx.strokeStyle = "rgba(99, 102, 241, 0.08)";
            ctx.lineWidth = 1.5;
            for (let x = 0; x < width; x += 10) {
                const y = Math.sin(x * 0.003 + step) * 45 + Math.cos(x * 0.002 + step * 0.5) * 35 + height * 0.35;
                if (x === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Draw ambient particles
            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0) p.x = width;
                if (p.x > width) p.x = 0;
                if (p.y < 0) p.y = height;
                if (p.y > height) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(129, 140, 248, ${p.alpha})`;
                ctx.fill();
            });

            requestAnimationFrame(animateCanvas);
        }
        animateCanvas();
    }

    // -------------------------------------------------------------------------
    // 3. Currency & Utility Helpers
    // -------------------------------------------------------------------------
    const formatINR = (num, includeDecimals = true) => {
        if (isNaN(num)) return "₹0";
        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            minimumFractionDigits: includeDecimals ? 2 : 0,
            maximumFractionDigits: includeDecimals ? 2 : 0
        }).format(num);
    };

    function showError(msg) {
        errorMessage.textContent = msg;
        errorBanner.style.display = "flex";
        errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function hideError() {
        errorBanner.style.display = "none";
    }

    if (dismissErrorBtn) {
        dismissErrorBtn.addEventListener("click", hideError);
    }

    // -------------------------------------------------------------------------
    // 4. Load Scenarios from Backend
    // -------------------------------------------------------------------------
    async function loadPresets() {
        try {
            const resp = await fetch(`${API_BASE_URL}/api/catalog-samples`);
            if (resp.ok) {
                sampleScenarios = await resp.json();
                sampleScenarios.forEach((item, idx) => {
                    const opt = document.createElement("option");
                    opt.value = idx;
                    opt.textContent = item.label || item.product_name;
                    presetSelect.appendChild(opt);
                });
            }
        } catch (err) {
            console.warn("Could not load scenarios from server:", err);
        }
    }

    // Auto-fill form when preset is chosen
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

        hideError();
        submitForm();
    });

    // -------------------------------------------------------------------------
    // 5. Form Submission & State Controller
    // -------------------------------------------------------------------------
    async function submitForm() {
        hideError();

        const costPrice = parseFloat(document.getElementById("costPrice").value);
        const currentPrice = parseFloat(document.getElementById("currentPrice").value);
        const mrp = parseFloat(document.getElementById("mrp").value);
        const compPrice = parseFloat(document.getElementById("competitorPrice").value);
        const stockLevel = parseInt(document.getElementById("stockLevel").value);
        const dailyOrders = parseInt(document.getElementById("dailyOrders").value);
        const daysToFestival = parseInt(document.getElementById("daysToFestival").value);

        // Validation Checks
        if (isNaN(costPrice) || costPrice <= 0) {
            showError("Please provide a valid positive Cost Price.");
            return;
        }
        if (isNaN(currentPrice) || currentPrice <= 0) {
            showError("Please provide a valid positive Current Selling Price.");
            return;
        }
        if (isNaN(mrp) || mrp <= 0) {
            showError("Please provide a valid Maximum Retail Price (MRP).");
            return;
        }
        if (costPrice > mrp) {
            showError(`Cost Price (${formatINR(costPrice)}) cannot exceed Maximum Retail Price MRP (${formatINR(mrp)}).`);
            return;
        }

        const payload = {
            product_id: "P001",
            product_name: document.getElementById("productName").value.trim() || "Product SKU",
            category: document.getElementById("categorySelect").value,
            city: document.getElementById("citySelect").value,
            cost_price: costPrice,
            current_price: currentPrice,
            mrp: mrp,
            competitor_avg_price: !isNaN(compPrice) && compPrice > 0 ? compPrice : currentPrice,
            stock_level: !isNaN(stockLevel) && stockLevel >= 0 ? stockLevel : 50,
            orders: !isNaN(dailyOrders) && dailyOrders >= 0 ? dailyOrders : 20,
            days_until_next_festival: !isNaN(daysToFestival) && daysToFestival >= 0 ? daysToFestival : 45,
            weather_type: document.getElementById("weatherType").value,
            competitor_stock_status: "In_Stock"
        };

        // UI Loading State
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
                const errJson = await resp.json().catch(() => ({}));
                throw new Error(errJson.detail || "We couldn't generate a recommendation right now. Please check your inputs.");
            }

            const data = await resp.json();
            renderRecommendation(data, payload);
        } catch (error) {
            showError(error.message || "We couldn't generate a recommendation right now. Please check the network connection and try again.");
        } finally {
            submitBtn.disabled = false;
            btnText.style.display = "flex";
            btnLoader.style.display = "none";
        }
    }

    // -------------------------------------------------------------------------
    // 6. Recommendation Results Renderer
    // -------------------------------------------------------------------------
    function renderRecommendation(data, payload) {
        // Toggle view from placeholder to results
        resultPlaceholder.style.display = "none";
        resultContent.style.display = "flex";

        // Product Subtitle
        resProductSubtitle.textContent = payload.product_name;

        // Prices & Changes
        const curr = data.current_price;
        const rec = data.recommended_price;
        const diff = data.price_change;
        const pct = data.price_change_percent !== undefined ? data.price_change_percent : data.price_change_percentage;

        resCurrentPrice.textContent = formatINR(curr);
        resRecommendedPrice.textContent = formatINR(rec);

        const sign = diff >= 0 ? "+" : "";
        resPriceDiff.textContent = `${sign}${formatINR(diff)}`;
        resPriceDiffPct.textContent = `${sign}${pct.toFixed(1)}%`;

        // Color coding for diff
        if (diff > 0) {
            resPriceDiff.style.color = "var(--accent-emerald)";
            resPriceDiffPct.style.color = "var(--accent-emerald)";
            resActionSummary.textContent = "Margin Expansion";
        } else if (diff < 0) {
            resPriceDiff.style.color = "#60a5fa";
            resPriceDiffPct.style.color = "#60a5fa";
            resActionSummary.textContent = "Volume Clearance";
        } else {
            resPriceDiff.style.color = "var(--accent-amber)";
            resPriceDiffPct.style.color = "var(--accent-amber)";
            resActionSummary.textContent = "Maintain Position";
        }

        // Action Badge Update
        const action = data.recommendation || (pct > 2 ? "Increase Price" : (pct < -2 ? "Decrease Price" : "Hold Price"));
        badgeText.textContent = action;
        resActionBadge.className = "action-badge";

        if (action === "Increase Price") {
            resActionBadge.classList.add("badge-increase");
            badgeIcon.textContent = "arrow_upward";
        } else if (action === "Decrease Price") {
            resActionBadge.classList.add("badge-decrease");
            badgeIcon.textContent = "arrow_downward";
        } else {
            resActionBadge.classList.add("badge-hold");
            badgeIcon.textContent = "horizontal_rule";
        }

        // Guardrail Limits & Pin Position
        const minP = data.min_allowed_price || (payload.cost_price * 1.05);
        const maxP = data.max_allowed_price || (payload.mrp * 1.05);
        const compP = payload.competitor_avg_price;

        resMinPrice.textContent = `Floor: ${formatINR(minP)}`;
        resCompPrice.textContent = `Market: ${formatINR(compP)}`;
        resMaxPrice.textContent = `Ceiling: ${formatINR(maxP)}`;
        pinTooltip.textContent = formatINR(rec);

        let pinPercent = 50;
        if (maxP > minP) {
            pinPercent = Math.max(8, Math.min(92, ((rec - minP) / (maxP - minP)) * 100));
        }
        guardrailPin.style.left = `${pinPercent}%`;

        // Insights List
        resInsightsList.innerHTML = "";
        const insights = data.insights && data.insights.length > 0
            ? data.insights
            : [
                "Recommended price maximizes profit margin within active market demand elasticity.",
                "Adheres strictly to guaranteed unit profit floor."
            ];

        insights.forEach(text => {
            const li = document.createElement("li");
            li.textContent = text;
            resInsightsList.appendChild(li);
        });

        // Inventory Runway Calculation & Badge
        const dailyOrders = Math.max(payload.orders, 0.5);
        const runwayDays = (payload.stock_level / dailyOrders).toFixed(1);
        resInventoryRunway.textContent = runwayDays;

        resInventoryStatusBadge.className = "stock-badge";
        if (runwayDays < 3.0) {
            resInventoryStatusBadge.classList.add("stock-low");
            resInventoryStatusText.textContent = "Low Stock";
        } else if (runwayDays > 45.0) {
            resInventoryStatusBadge.classList.add("stock-high");
            resInventoryStatusText.textContent = "High Stock";
        } else {
            resInventoryStatusBadge.classList.add("stock-good");
            resInventoryStatusText.textContent = "Healthy Stock";
        }

        // Mobile Scroll To Result
        if (window.innerWidth < 1100) {
            resultContent.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    // -------------------------------------------------------------------------
    // 7. Event Listeners
    // -------------------------------------------------------------------------
    form.addEventListener("submit", (e) => {
        e.preventDefault();
        submitForm();
    });

    // Initialize presets on startup
    loadPresets();
});
