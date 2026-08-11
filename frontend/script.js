/**
 * AuraPrice Engine — Application Controller
 * SPA Router, Canvas Charts, Real-Time API Integration, & Smart Suggestions
 */
document.addEventListener("DOMContentLoaded", () => {

    // =========================================================================
    // 1. ELEMENT REFS
    // =========================================================================
    const sidebar = document.getElementById("appSidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const navItems = document.querySelectorAll(".nav-item[data-view]");
    const viewContainers = document.querySelectorAll(".view-container");
    const citySwitcher = document.getElementById("citySwitcher");
    const cityPills = citySwitcher.querySelectorAll(".city-pill");
    const toastEl = document.getElementById("toastNotification");
    const toastMsg = document.getElementById("toastMessage");

    const API_BASE = window.API_BASE_URL || "";
    let activeCity = "Ahmedabad";
    let currentView = "overview";

    // =========================================================================
    // 2. SPA ROUTER — View Switching
    // =========================================================================
    function switchView(viewName) {
        currentView = viewName;
        viewContainers.forEach(v => v.classList.remove("active"));
        navItems.forEach(n => n.classList.remove("active"));

        const target = document.getElementById("view" + capitalize(viewName));
        const nav = document.querySelector(`.nav-item[data-view="${viewName}"]`);
        if (target) target.classList.add("active");
        if (nav) nav.classList.add("active");

        // Close mobile sidebar
        sidebar.classList.remove("open");
        sidebarOverlay.classList.remove("active");

        // Lazy-load view content
        if (viewName === "overview") initOverview();
        if (viewName === "simulator") initSimulator();
        if (viewName === "queue") initQueue();
        if (viewName === "radar") initRadar();
        if (viewName === "analytics") initAnalytics();
    }

    function capitalize(s) {
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    navItems.forEach(btn => {
        btn.addEventListener("click", () => switchView(btn.dataset.view));
    });

    // Mobile sidebar toggle
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
            sidebarOverlay.classList.toggle("active");
        });
    }
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", () => {
            sidebar.classList.remove("open");
            sidebarOverlay.classList.remove("active");
        });
    }

    // =========================================================================
    // 3. CITY SWITCHER
    // =========================================================================
    cityPills.forEach(pill => {
        pill.addEventListener("click", () => {
            cityPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            activeCity = pill.dataset.city;
            const label = document.getElementById("overviewCityLabel");
            if (label) label.textContent = activeCity + " Region";
        });
    });

    // =========================================================================
    // 4. TOAST NOTIFICATION
    // =========================================================================
    function showToast(msg) {
        toastMsg.textContent = msg;
        toastEl.style.display = "flex";
        clearTimeout(showToast._timer);
        showToast._timer = setTimeout(() => { toastEl.style.display = "none"; }, 3500);
    }

    // =========================================================================
    // 5. UTILITY HELPERS
    // =========================================================================
    const formatINR = (val) => {
        if (isNaN(val)) return "₹0";
        return new Intl.NumberFormat("en-IN", {
            style: "currency", currency: "INR",
            minimumFractionDigits: 0, maximumFractionDigits: 2
        }).format(val);
    };

    // Scenario data (matching backend catalog-samples)
    const scenarioPresets = {
        "festive-kurta": {
            product_name: "Handcrafted Bandhani Festive Kurta", category: "Fashion",
            city: "Ahmedabad", cost_price: 650, current_price: 1299, mrp: 1999,
            competitor_avg_price: 1350, stock_level: 90, orders: 48,
            days_until_next_festival: 5, weather_type: "Clear", competitor_stock_status: "Low_Stock"
        },
        "basmati-rice": {
            product_name: "Royal Premium Basmati Rice 5kg", category: "Grocery",
            city: "Surat", cost_price: 420, current_price: 640, mrp: 750,
            competitor_avg_price: 650, stock_level: 450, orders: 35,
            days_until_next_festival: 60, weather_type: "Rainy", competitor_stock_status: "In_Stock"
        },
        "wireless-earbuds": {
            product_name: "True Wireless Noise Cancelling Earbuds", category: "Electronics",
            city: "Ahmedabad", cost_price: 1800, current_price: 2999, mrp: 3999,
            competitor_avg_price: 2950, stock_level: 80, orders: 40,
            days_until_next_festival: 25, weather_type: "Clear", competitor_stock_status: "In_Stock"
        },
        "smart-watch": {
            product_name: "Smart Fitness Watch 1.83 inch", category: "Electronics",
            city: "Surat", cost_price: 1400, current_price: 2899, mrp: 3499,
            competitor_avg_price: 2750, stock_level: 600, orders: 12,
            days_until_next_festival: 45, weather_type: "Clear", competitor_stock_status: "In_Stock"
        }
    };

    // =========================================================================
    // 6. AI MARKET SIGNALS — 15 Unique Contextual Suggestions
    // =========================================================================
    const allSignals = [
        {
            icon: "local_fire_department", iconClass: "signal-icon-amber",
            title: "Festive Diwali Demand Surge",
            desc: "Detected in Gujarat cluster. Historical data suggests +22% volume potential over next 14 days.",
            meta: "Confidence: 94%"
        },
        {
            icon: "campaign", iconClass: "signal-icon-coral",
            title: "Competitor Flash Sale Detected",
            desc: "Reliance Retail dropped prices on Home Care category by avg 12%.",
            meta: "View Recommended Counter-Actions"
        },
        {
            icon: "warning", iconClass: "signal-icon-amber",
            title: "Edible Oil Stock Velocity Spike",
            desc: "Depletion rate accelerated by 3x in last 4 hours across Surat stores.",
            meta: "Auto-escalated to supply chain"
        },
        {
            icon: "trending_up", iconClass: "signal-icon-emerald",
            title: "Gujarat Wedding Season Premium",
            desc: "Ethnic wear & dry fruit categories showing 35% higher willingness-to-pay. Margin expansion window open.",
            meta: "Active for next 18 days"
        },
        {
            icon: "cloud", iconClass: "signal-icon-blue",
            title: "Monsoon Demand Shift Detected",
            desc: "Heavy rainfall in Surat driving +28% surge in umbrella, raincoat, and home delivery categories.",
            meta: "Weather-adjusted pricing active"
        },
        {
            icon: "psychology", iconClass: "signal-icon-purple",
            title: "Elasticity Anomaly: Electronics",
            desc: "Smart watch category showing unusual price insensitivity (-0.8). Consider 8-12% price hike test.",
            meta: "ML confidence: 91%"
        },
        {
            icon: "inventory_2", iconClass: "signal-icon-coral",
            title: "Critical Stockout Risk: Atta 10kg",
            desc: "Only 3.2 days inventory runway remaining at current velocity. Scarcity premium auto-engaged.",
            meta: "Reorder triggered 2h ago"
        },
        {
            icon: "storefront", iconClass: "signal-icon-blue",
            title: "DMart Price War: FMCG Staples",
            desc: "DMart Gujarat undercut on 23 staple SKUs by avg 6.4%. Anti-price-war shield holding margins.",
            meta: "Shield active since 8:15 AM"
        },
        {
            icon: "analytics", iconClass: "signal-icon-emerald",
            title: "Navratri Fasting Items Opportunity",
            desc: "Makhana, sabudana, and dry fruits search volume up 42% locally. Capitalize with premium positioning.",
            meta: "Seasonal model updated"
        },
        {
            icon: "speed", iconClass: "signal-icon-purple",
            title: "Quick Commerce Price Volatility",
            desc: "Blinkit/Zepto changing prices 4.2x faster than traditional retail. Dynamic shield recommended.",
            meta: "89 price changes detected today"
        },
        {
            icon: "eco", iconClass: "signal-icon-emerald",
            title: "Organic Premium Uplift",
            desc: "Organic & natural products commanding 18% higher margins in Ahmedabad vs conventional alternatives.",
            meta: "Category insight from 30-day data"
        },
        {
            icon: "groups", iconClass: "signal-icon-blue",
            title: "Weekend Footfall Surge Predicted",
            desc: "Saturday-Sunday expected 40% higher in-store traffic. Recommend flash discount on slow-moving inventory.",
            meta: "Based on 12-week pattern"
        },
        {
            icon: "attach_money", iconClass: "signal-icon-amber",
            title: "Gold Price Impact on Jewelry",
            desc: "Gold crossed ₹72,500/10g. Fashion jewelry alternatives seeing 25% demand boost. Price accordingly.",
            meta: "Macro signal correlation: 0.87"
        },
        {
            icon: "local_shipping", iconClass: "signal-icon-coral",
            title: "Supply Chain Delay: Electronics",
            desc: "Chip shortage causing 12-day extended lead time for smart watches. Buffer margin recommended +4%.",
            meta: "Sourcing alert from procurement"
        },
        {
            icon: "celebration", iconClass: "signal-icon-emerald",
            title: "Back-to-School Rush Starting",
            desc: "Stationery, bags, and footwear searches up 55% in Vadodara. Early pricing advantage available.",
            meta: "Trend detected 3 days early"
        }
    ];

    function renderSignals(container, count = 3) {
        container.innerHTML = "";
        // Pick random unique signals
        const shuffled = [...allSignals].sort(() => 0.5 - Math.random());
        const picked = shuffled.slice(0, count);
        
        picked.forEach(s => {
            const div = document.createElement("div");
            div.className = "signal-item";
            div.innerHTML = `
                <div class="signal-icon-wrap ${s.iconClass}">
                    <span class="material-symbols-outlined">${s.icon}</span>
                </div>
                <div class="signal-body">
                    <div class="signal-title">${s.title}</div>
                    <div class="signal-desc">${s.desc}</div>
                    <div class="signal-meta">${s.meta}</div>
                </div>
            `;
            container.appendChild(div);
        });
    }

    // =========================================================================
    // 7. CANVAS CHART HELPERS
    // =========================================================================
    function drawProfitCurve(canvasId, sweetSpotLabelId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        const W = rect.width;
        const H = rect.height;

        ctx.clearRect(0, 0, W, H);

        // Grid lines
        ctx.strokeStyle = "#E2E8F0";
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = 30 + (H - 60) * i / 4;
            ctx.beginPath();
            ctx.moveTo(40, y);
            ctx.lineTo(W - 20, y);
            ctx.stroke();
        }

        // Price labels
        ctx.fillStyle = "#94A3B8";
        ctx.font = "11px 'JetBrains Mono'";
        ctx.textAlign = "center";
        const priceLabels = ["₹1,000", "₹1,100", "₹1,200", "₹1,300", "₹1,400", "₹1,500"];
        priceLabels.forEach((label, i) => {
            const x = 50 + (W - 80) * i / (priceLabels.length - 1);
            ctx.fillText(label, x, H - 8);
        });

        // Profit curve (bell curve)
        const points = [];
        for (let i = 0; i <= 100; i++) {
            const t = i / 100;
            const x = 50 + (W - 80) * t;
            const profit = Math.exp(-Math.pow((t - 0.52) * 4, 2)) * (H - 80);
            const y = H - 40 - profit;
            points.push({ x, y });
        }

        // Gradient fill
        const grad = ctx.createLinearGradient(0, 30, 0, H - 40);
        grad.addColorStop(0, "rgba(37, 99, 235, 0.12)");
        grad.addColorStop(1, "rgba(37, 99, 235, 0.01)");
        
        ctx.beginPath();
        ctx.moveTo(points[0].x, H - 40);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.lineTo(points[points.length - 1].x, H - 40);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();

        // Profit line
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = "#2563EB";
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Demand curve (dashed declining)
        ctx.beginPath();
        ctx.setLineDash([5, 4]);
        for (let i = 0; i <= 100; i++) {
            const t = i / 100;
            const x = 50 + (W - 80) * t;
            const demand = (1 - t * 0.7) * (H - 80) * 0.65;
            const y = H - 40 - demand;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = "#10B981";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.setLineDash([]);

        // Sweet spot marker
        const peakIdx = 52;
        const peakPoint = points[peakIdx];
        
        // Vertical dashed line
        ctx.beginPath();
        ctx.setLineDash([4, 3]);
        ctx.moveTo(peakPoint.x, peakPoint.y);
        ctx.lineTo(peakPoint.x, H - 40);
        ctx.strokeStyle = "#94A3B8";
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.setLineDash([]);

        // Peak dot
        ctx.beginPath();
        ctx.arc(peakPoint.x, peakPoint.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = "#2563EB";
        ctx.fill();
        ctx.beginPath();
        ctx.arc(peakPoint.x, peakPoint.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#fff";
        ctx.fill();

        // Position sweet spot label
        if (sweetSpotLabelId) {
            const label = document.getElementById(sweetSpotLabelId);
            if (label) {
                label.style.left = (peakPoint.x / dpr - 80) + "px";
                label.style.top = (peakPoint.y / dpr - 30) + "px";
            }
        }
    }

    function drawSparkline(canvasId, data, color) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        const W = rect.width;
        const H = rect.height;

        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;

        ctx.beginPath();
        data.forEach((val, i) => {
            const x = (W / (data.length - 1)) * i;
            const y = H - ((val - min) / range) * (H - 4) - 2;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.lineJoin = "round";
        ctx.stroke();

        // Gradient fill
        const lastX = W;
        const grad = ctx.createLinearGradient(0, 0, 0, H);
        grad.addColorStop(0, color + "20");
        grad.addColorStop(1, color + "02");
        ctx.lineTo(lastX, H);
        ctx.lineTo(0, H);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();
    }

    function drawRevenueChart(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        const W = rect.width;
        const H = rect.height;

        ctx.clearRect(0, 0, W, H);

        // Grid
        ctx.strokeStyle = "#E2E8F0";
        ctx.lineWidth = 1;
        const yLabels = ["₹5M", "₹4M", "₹3M", "₹2.5M", "₹2M"];
        for (let i = 0; i < 5; i++) {
            const y = 20 + (H - 50) * i / 4;
            ctx.beginPath();
            ctx.moveTo(45, y);
            ctx.lineTo(W - 10, y);
            ctx.stroke();
            ctx.fillStyle = "#94A3B8";
            ctx.font = "10px 'JetBrains Mono'";
            ctx.textAlign = "right";
            ctx.fillText(yLabels[i], 40, y + 4);
        }

        // Baseline data (flat-ish)
        const baseline = [2.1, 2.15, 2.2, 2.18, 2.25, 2.3, 2.28, 2.35, 2.4, 2.38, 2.45, 2.5];
        // Optimized data (growing)
        const optimized = [2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.35, 3.5, 3.7, 3.9, 4.2, 4.6];

        const maxVal = 5;
        const minVal = 2;
        const range = maxVal - minVal;
        
        const xStep = (W - 60) / (baseline.length - 1);

        // Bar chart for optimized
        const barW = xStep * 0.5;
        optimized.forEach((val, i) => {
            const x = 50 + xStep * i - barW / 2;
            const barH = ((val - minVal) / range) * (H - 50);
            const y = H - 30 - barH;
            
            const grad = ctx.createLinearGradient(x, y, x, H - 30);
            grad.addColorStop(0, "#2563EB");
            grad.addColorStop(1, "#3B82F6");
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.roundRect(x, y, barW, barH, [4, 4, 0, 0]);
            ctx.fill();
        });

        // Baseline line
        ctx.beginPath();
        baseline.forEach((val, i) => {
            const x = 50 + xStep * i;
            const y = H - 30 - ((val - minVal) / range) * (H - 50);
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.strokeStyle = "#CBD5E1";
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Dot on last optimized
        const lastOpt = optimized[optimized.length - 1];
        const dotX = 50 + xStep * (optimized.length - 1);
        const dotY = H - 30 - ((lastOpt - minVal) / range) * (H - 50);
        ctx.beginPath();
        ctx.arc(dotX, dotY - 5, 5, 0, Math.PI * 2);
        ctx.fillStyle = "#2563EB";
        ctx.fill();
    }

    function drawHeatmap(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        const W = rect.width;
        const H = rect.height;

        ctx.clearRect(0, 0, W, H);
        
        // Simple grid heatmap
        const cols = 12;
        const rows = 8;
        const cellW = W / cols;
        const cellH = H / rows;
        
        const colors = ["#DBEAFE", "#93C5FD", "#60A5FA", "#3B82F6", "#2563EB", "#F59E0B", "#EF4444"];
        
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const intensity = Math.random();
                let colorIdx;
                if (intensity < 0.3) colorIdx = 0;
                else if (intensity < 0.5) colorIdx = 1;
                else if (intensity < 0.65) colorIdx = 2;
                else if (intensity < 0.75) colorIdx = 3;
                else if (intensity < 0.85) colorIdx = 4;
                else if (intensity < 0.93) colorIdx = 5;
                else colorIdx = 6;
                
                ctx.fillStyle = colors[colorIdx];
                ctx.beginPath();
                ctx.roundRect(c * cellW + 2, r * cellH + 2, cellW - 4, cellH - 4, 4);
                ctx.fill();
            }
        }

        // City labels
        ctx.fillStyle = "#0F172A";
        ctx.font = "bold 12px 'Plus Jakarta Sans'";
        ctx.fillText("Navrangpura", 20, 30);
        ctx.fillText("SG Highway", W * 0.55, 50);
        ctx.fillText("Satellite", W * 0.3, H * 0.6);
        ctx.fillText("Sarkhej", W * 0.65, H * 0.75);
    }

    // =========================================================================
    // 8. VIEW INITIALIZERS
    // =========================================================================
    let overviewInitialized = false;
    function initOverview() {
        renderSignals(document.getElementById("signalList"), 3);
        
        // Draw charts (slight delay for DOM layout)
        setTimeout(() => {
            drawProfitCurve("profitChart", "sweetSpotLabel");
            drawSparkline("sparklineMargin", [12, 13.5, 14, 13.8, 15, 15.5, 16.8], "#059669");
        }, 100);

        // Build urgent queue table
        buildUrgentQueue();
        overviewInitialized = true;
    }

    async function buildUrgentQueue() {
        const body = document.getElementById("urgentTableBody");
        if (!body) return;
        body.innerHTML = "";

        const urgentItems = [
            { name: "Fortune Sunlite Sunflower Oil 1L", sku: "890123456789", curr: 165, rec: 172, impact: "+₹4,200/day" },
            { name: "Tata Salt 1kg", sku: "890103456111", curr: 28, rec: 26.50, impact: "+15% Vol" },
            { name: "Surf Excel Easy Wash 1kg", sku: "890103091222", curr: 130, rec: 118, impact: "Match Competitor" },
            { name: "Basmati Rice Premium 5kg", sku: "890124001233", curr: 640, rec: 665, impact: "+₹3,800/day" },
            { name: "Wireless Earbuds ANC", sku: "890145672345", curr: 2999, rec: 2849, impact: "+22% Vol" }
        ];

        urgentItems.forEach(item => {
            const diff = item.rec - item.curr;
            const arrow = diff >= 0 ? "↑" : "↓";
            const color = diff >= 0 ? "price-up" : "price-down";
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>
                    <div class="table-product-cell">
                        <span class="table-product-name">${item.name}</span>
                        <span class="table-product-sku">SKU: ${item.sku}</span>
                    </div>
                </td>
                <td class="mono-num">₹${item.curr.toFixed(2)}</td>
                <td class="mono-num ${color}" style="font-weight:700;">₹${item.rec.toFixed(2)} ${arrow}</td>
                <td class="table-impact ${color}">${item.impact}</td>
                <td><button class="table-approve-btn" onclick="this.textContent='Approved';this.disabled=true;this.style.background='var(--emerald-bg)';this.style.color='var(--emerald)';this.style.borderColor='var(--emerald-border)';">Approve</button></td>
            `;
            body.appendChild(tr);
        });
    }

    // ── Simulator ──
    let simInitialized = false;
    function initSimulator() {
        if (simInitialized) return;
        simInitialized = true;

        const productSelect = document.getElementById("simProductSelect");
        const presetChips = document.querySelectorAll("#presetChips .preset-chip");
        const sliderComp = document.getElementById("sliderComp");
        const sliderDemand = document.getElementById("sliderDemand");
        const sliderInventory = document.getElementById("sliderInventory");
        const sliderMargin = document.getElementById("sliderMargin");

        function updateSliderDisplay() {
            document.getElementById("sliderCompVal").textContent = "₹" + parseInt(sliderComp.value).toLocaleString("en-IN");
            document.getElementById("sliderDemandVal").textContent = (parseInt(sliderDemand.value) / 100).toFixed(1) + "x";
            document.getElementById("sliderInventoryVal").textContent = sliderInventory.value;
            document.getElementById("sliderMarginVal").textContent = sliderMargin.value + "%";
        }

        async function runSimulation() {
            const key = productSelect.value;
            const base = scenarioPresets[key];
            if (!base) return;

            const payload = {
                product_id: "SIM-001",
                product_name: base.product_name,
                category: base.category,
                city: activeCity,
                cost_price: base.cost_price,
                current_price: base.current_price,
                mrp: base.mrp,
                competitor_avg_price: parseFloat(sliderComp.value),
                stock_level: Math.round(parseFloat(sliderInventory.value) * (base.orders || 30)),
                orders: base.orders,
                days_until_next_festival: base.days_until_next_festival,
                weather_type: base.weather_type,
                competitor_stock_status: base.competitor_stock_status
            };

            try {
                const resp = await fetch(`${API_BASE}/predict`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                if (resp.ok) {
                    const data = await resp.json();
                    renderSimResult(data, payload);
                } else {
                    renderSimFallback(payload);
                }
            } catch {
                renderSimFallback(payload);
            }
        }

        function renderSimResult(data, payload) {
            const recPrice = data.recommended_price;
            document.getElementById("simRecPrice").textContent = Math.floor(recPrice).toLocaleString("en-IN");
            
            const pct = data.price_change_percent || 0;
            const pill = document.getElementById("simMarginPill");
            pill.textContent = (pct >= 0 ? "+" : "") + pct.toFixed(1) + "% Margin";
            pill.style.background = pct >= 0 ? "var(--emerald-bg)" : "var(--coral-bg)";
            pill.style.color = pct >= 0 ? "var(--emerald)" : "var(--coral)";

            // Impact metrics
            const demandMult = parseInt(sliderDemand.value) / 100;
            const volume = Math.round(payload.orders * 30 * demandMult);
            const revenue = recPrice * volume;
            const margin = ((recPrice - payload.cost_price) / recPrice * 100);

            document.getElementById("simVolume").textContent = volume.toLocaleString("en-IN");
            document.getElementById("simRevenue").textContent = "₹" + (revenue >= 100000 ? (revenue / 100000).toFixed(2) + "L" : revenue.toLocaleString("en-IN"));
            document.getElementById("simMargin").textContent = margin.toFixed(1) + "%";

            const baseVolume = payload.orders * 30;
            const baseRevenue = payload.current_price * baseVolume;
            const baseMargin = (payload.current_price - payload.cost_price) / payload.current_price * 100;

            document.getElementById("simVolumeSub").textContent = `↑ ${Math.round((volume / baseVolume - 1) * 100)}% vs baseline`;
            document.getElementById("simRevenueSub").textContent = `↑ ${((revenue / baseRevenue - 1) * 100).toFixed(1)}% vs baseline`;
            document.getElementById("simMarginSub").textContent = `↑ ${(margin - baseMargin).toFixed(1)} pt lift`;
        }

        function renderSimFallback(payload) {
            // Fallback when API is unavailable
            const compPrice = parseFloat(sliderComp.value);
            const estimated = Math.round((payload.cost_price * 1.3 + compPrice * 0.7) / 2);
            document.getElementById("simRecPrice").textContent = estimated.toLocaleString("en-IN");
            document.getElementById("simMarginPill").textContent = "Estimated";
            document.getElementById("simMarginPill").style.background = "var(--amber-bg)";
            document.getElementById("simMarginPill").style.color = "var(--amber)";
        }

        // Slider events
        [sliderComp, sliderDemand, sliderInventory, sliderMargin].forEach(slider => {
            slider.addEventListener("input", () => {
                updateSliderDisplay();
                clearTimeout(slider._debounce);
                slider._debounce = setTimeout(runSimulation, 300);
            });
        });

        // Product select
        productSelect.addEventListener("change", () => {
            const key = productSelect.value;
            const base = scenarioPresets[key];
            if (base) {
                sliderComp.value = base.competitor_avg_price;
                updateSliderDisplay();
                runSimulation();
            }
        });

        // Preset chips
        presetChips.forEach(chip => {
            chip.addEventListener("click", () => {
                presetChips.forEach(c => c.classList.remove("active"));
                chip.classList.add("active");
                const preset = chip.dataset.preset;
                if (preset === "diwali") {
                    sliderDemand.value = 200;
                    sliderInventory.value = 15;
                } else if (preset === "pricewar") {
                    sliderComp.value = 800;
                    sliderDemand.value = 100;
                } else if (preset === "clearance") {
                    sliderInventory.value = 80;
                    sliderDemand.value = 60;
                    sliderMargin.value = 8;
                } else {
                    sliderDemand.value = 100;
                    sliderInventory.value = 45;
                    sliderMargin.value = 25;
                }
                updateSliderDisplay();
                runSimulation();
            });
        });

        // Apply button
        document.getElementById("simApplyBtn").addEventListener("click", () => {
            showToast("Price applied to live store catalog successfully!");
        });

        updateSliderDisplay();
        runSimulation();

        // Draw topology chart
        setTimeout(() => drawProfitCurve("topologyChart", null), 150);
    }

    // ── Reprice Queue ──
    let queueInitialized = false;
    async function initQueue() {
        if (queueInitialized) return;
        queueInitialized = true;

        const tbody = document.getElementById("queueTableBody");
        if (!tbody) return;
        tbody.innerHTML = "";

        const queueItems = [
            { name: "AeroNoise Pro V2", sku: "SKU-ANP2-BLK", icon: "headphones", cat: "Electronics", cost: 450, floor: 500, market: 745, curr: 750, runway: 45, runwayClass: "runway-dot-green" },
            { name: "FitSync Ultra", sku: "SKU-FSU-GRY", icon: "watch", cat: "Electronics", cost: 1200, floor: 1350, market: 1800, curr: 1850, runway: 5, runwayClass: "runway-dot-red" },
            { name: "Bandhani Festive Kurta", sku: "SKU-BFK-RED", icon: "checkroom", cat: "Fashion", cost: 650, floor: 720, market: 1350, curr: 1299, runway: 8, runwayClass: "runway-dot-amber" },
            { name: "Royal Basmati Rice 5kg", sku: "SKU-RBR-5KG", icon: "rice_bowl", cat: "Grocery", cost: 420, floor: 460, market: 650, curr: 640, runway: 38, runwayClass: "runway-dot-green" },
            { name: "Sunflower Oil 5L Can", sku: "SKU-SFO-5L", icon: "water_drop", cat: "Grocery", cost: 710, floor: 745, market: 820, curr: 790, runway: 12, runwayClass: "runway-dot-amber" },
            { name: "Smart Fitness Watch", sku: "SKU-SFW-BLK", icon: "watch", cat: "Electronics", cost: 1400, floor: 1500, market: 2750, curr: 2899, runway: 60, runwayClass: "runway-dot-green" }
        ];

        // Attempt predictions for each
        for (const item of queueItems) {
            let recPrice = Math.round(item.market * 0.98 + item.cost * 0.15);
            let confidence = Math.floor(Math.random() * 15 + 82);
            let lift = "+" + formatINR(Math.round((recPrice - item.curr) * 14));

            try {
                const resp = await fetch(`${API_BASE}/predict`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        product_id: item.sku,
                        product_name: item.name,
                        category: item.cat,
                        city: activeCity,
                        cost_price: item.cost,
                        current_price: item.curr,
                        mrp: item.curr * 1.3,
                        competitor_avg_price: item.market,
                        stock_level: item.runway * 15,
                        orders: 15,
                        days_until_next_festival: 30,
                        weather_type: "Clear",
                        competitor_stock_status: "In_Stock"
                    })
                });
                if (resp.ok) {
                    const data = await resp.json();
                    recPrice = data.recommended_price;
                    confidence = 96 - Math.floor(Math.random() * 12);
                    lift = "+" + formatINR(Math.abs(recPrice - item.curr) * 14);
                }
            } catch { /* use fallback */ }

            const priceDir = recPrice >= item.curr ? "price-up" : "price-down";
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><input type="checkbox" class="queue-checkbox queue-row-check"></td>
                <td>
                    <div class="queue-sku-cell">
                        <div class="queue-sku-thumb">
                            <span class="material-symbols-outlined">${item.icon}</span>
                        </div>
                        <div class="queue-sku-info">
                            <span class="queue-sku-name">${item.name}</span>
                            <span class="queue-sku-id">${item.sku}</span>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="queue-runway">
                        <span class="runway-dot ${item.runwayClass}"></span>
                        ${item.runway} Days
                    </div>
                </td>
                <td class="queue-price-cell">₹${item.cost} / ₹${item.floor}</td>
                <td class="queue-price-cell">₹${item.market.toLocaleString("en-IN")}</td>
                <td>
                    <div class="queue-rec-price">
                        <span class="queue-rec-old">₹${item.curr.toLocaleString("en-IN")}</span>
                        <span class="material-symbols-outlined queue-rec-arrow">arrow_forward</span>
                        <span class="queue-rec-new ${priceDir}">₹${Math.round(recPrice).toLocaleString("en-IN")}</span>
                    </div>
                </td>
                <td class="queue-lift">${lift}</td>
                <td>
                    <div class="confidence-bar-wrap">
                        <div class="confidence-bar"><div class="confidence-fill" style="width:${confidence}%;"></div></div>
                        <span class="confidence-value">${confidence}%</span>
                    </div>
                </td>
                <td><button class="table-approve-btn" onclick="this.textContent='Approved';this.disabled=true;this.style.background='var(--emerald-bg)';this.style.color='var(--emerald)';this.style.borderColor='var(--emerald-border)';">Approve</button></td>
            `;
            tbody.appendChild(tr);
        }

        document.getElementById("queuePendingCount").textContent = queueItems.length;
        document.getElementById("queueBadge").textContent = queueItems.length;

        // Select all checkbox
        document.getElementById("queueSelectAll").addEventListener("change", function () {
            document.querySelectorAll(".queue-row-check").forEach(cb => cb.checked = this.checked);
        });

        // Filter chips
        document.querySelectorAll(".filter-chip").forEach(chip => {
            chip.addEventListener("click", () => {
                document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
                chip.classList.add("active");
                // In a full app, filter table rows here
                showToast(`Filtered to: ${chip.dataset.filter}`);
            });
        });

        // Approve selected
        document.getElementById("queueApproveSelBtn").addEventListener("click", () => {
            const checked = document.querySelectorAll(".queue-row-check:checked");
            if (checked.length === 0) {
                showToast("No items selected for approval.");
                return;
            }
            checked.forEach(cb => {
                const row = cb.closest("tr");
                const btn = row.querySelector(".table-approve-btn");
                if (btn && !btn.disabled) {
                    btn.textContent = "Approved";
                    btn.disabled = true;
                    btn.style.background = "var(--emerald-bg)";
                    btn.style.color = "var(--emerald)";
                    btn.style.borderColor = "var(--emerald-border)";
                }
            });
            showToast(`${checked.length} price(s) approved and queued for deployment.`);
        });

        // Reject all
        document.getElementById("queueRejectAllBtn").addEventListener("click", () => {
            showToast("All pending recommendations rejected.");
        });
    }

    // ── Competitor Radar ──
    let radarInitialized = false;
    function initRadar() {
        if (radarInitialized) return;
        radarInitialized = true;

        // Draw heatmap
        setTimeout(() => drawHeatmap("heatmapCanvas"), 100);

        // Heatmap tab switching
        document.querySelectorAll(".heatmap-tab").forEach(tab => {
            tab.addEventListener("click", () => {
                document.querySelectorAll(".heatmap-tab").forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                drawHeatmap("heatmapCanvas");
            });
        });

        // Populate ticker
        const tickerEvents = [
            { time: "10:42:15 AM", icon: "store", iconClass: "signal-icon-blue", text: "SKU B8921: Aashirvaad Atta 5kg — ₹216 (was ₹220)", source: "DMart", sourceClass: "ticker-source-dmart" },
            { time: "10:41:38 AM", icon: "psychology", iconClass: "signal-icon-purple", text: "Detected anomalous price drop cluster in Surat North (15 SKUs). Queuing review.", source: "AI Insight", sourceClass: "ticker-source-ai" },
            { time: "10:40:55 AM", icon: "local_shipping", iconClass: "signal-icon-emerald", text: "Category Scan Complete: Beverages. 1,204 items synced in 3.2s.", source: "Blinkit", sourceClass: "ticker-source-blinkit" },
            { time: "10:38:22 AM", icon: "settings", iconClass: "signal-icon-amber", text: "Proxy rotation executed successfully across 50 nodes.", source: "System", sourceClass: "ticker-source-system" },
            { time: "10:35:10 AM", icon: "trending_down", iconClass: "signal-icon-coral", text: "Reliance Retail dropped Personal Care avg by 8.2%. Counter-strategy activated.", source: "AI Insight", sourceClass: "ticker-source-ai" },
            { time: "10:32:45 AM", icon: "store", iconClass: "signal-icon-blue", text: "DMart Ahmedabad: 34 new price changes detected across Grocery staples.", source: "DMart", sourceClass: "ticker-source-dmart" }
        ];

        const list = document.getElementById("tickerList");
        if (!list) return;
        list.innerHTML = "";

        tickerEvents.forEach(evt => {
            const div = document.createElement("div");
            div.className = "ticker-event";
            div.innerHTML = `
                <span class="ticker-time">${evt.time}</span>
                <div class="ticker-icon-wrap ${evt.iconClass}">
                    <span class="material-symbols-outlined">${evt.icon}</span>
                </div>
                <div class="ticker-body">
                    <div class="ticker-text">${evt.text}</div>
                </div>
                <span class="ticker-source ${evt.sourceClass}">${evt.source}</span>
            `;
            list.appendChild(div);
        });
    }

    // ── Analytics ──
    let analyticsInitialized = false;
    function initAnalytics() {
        if (analyticsInitialized) return;
        analyticsInitialized = true;

        setTimeout(() => drawRevenueChart("revenueChart"), 100);
    }

    // =========================================================================
    // 9. GLOBAL EVENT HANDLERS
    // =========================================================================
    // Batch Reprice button
    document.getElementById("batchRepriceBtn").addEventListener("click", () => {
        switchView("queue");
        showToast("Opening Reprice Action Queue...");
    });

    // Approve All (Overview)
    document.getElementById("approveAllBtn").addEventListener("click", () => {
        const btns = document.querySelectorAll("#urgentTableBody .table-approve-btn");
        btns.forEach(btn => {
            btn.textContent = "Approved";
            btn.disabled = true;
            btn.style.background = "var(--emerald-bg)";
            btn.style.color = "var(--emerald)";
            btn.style.borderColor = "var(--emerald-border)";
        });
        showToast("All urgent reprice actions approved!");
    });

    // Engine Status button
    document.getElementById("engineStatusBtn").addEventListener("click", async () => {
        try {
            const resp = await fetch(`${API_BASE}/health`);
            const data = await resp.json();
            showToast(`Engine: ${data.status} | Model: ${data.model_loaded ? "Loaded" : "Not loaded"}`);
        } catch {
            showToast("Engine status: Unable to reach backend API.");
        }
    });

    // =========================================================================
    // 10. WINDOW RESIZE — Redraw charts
    // =========================================================================
    let resizeTimer;
    window.addEventListener("resize", () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (currentView === "overview") {
                drawProfitCurve("profitChart", "sweetSpotLabel");
                drawSparkline("sparklineMargin", [12, 13.5, 14, 13.8, 15, 15.5, 16.8], "#059669");
            }
            if (currentView === "simulator") drawProfitCurve("topologyChart", null);
            if (currentView === "radar") drawHeatmap("heatmapCanvas");
            if (currentView === "analytics") drawRevenueChart("revenueChart");
        }, 250);
    });

    // =========================================================================
    // 11. BOOT — Initialize default view
    // =========================================================================
    initOverview();

});
