"""
Product catalog definition with 130 realistic SKUs across 8 categories and 9 launch cohorts.
"""
from typing import List, Dict, Any
from .config import COHORT_SCHEDULE, CATEGORY_CONFIG

def build_product_catalog() -> List[Dict[str, Any]]:
    """
    Constructs the master list of 130 products with pricing baselines,
    cost structures, inventory policies, and cohort launch dates.
    """
    raw_products = [
        # --- 1. Electronics (18 SKUs) ---
        {"name": "Wireless Noise Cancelling Headphones Pro", "brand": "SoundPulse", "cat": "Electronics", "subcat": "Audio", "mrp": 4999.0, "cost_ratio": 0.52, "base_stock": 180, "lead_time": 7, "restock_cost": 25000.0, "base_views": 1500},
        {"name": "Portable Bluetooth Speaker 20W", "brand": "SoundPulse", "cat": "Electronics", "subcat": "Audio", "mrp": 2499.0, "cost_ratio": 0.55, "base_stock": 220, "lead_time": 6, "restock_cost": 15000.0, "base_views": 1800},
        {"name": "True Wireless Earbuds with ANC", "brand": "AuraAudio", "cat": "Electronics", "subcat": "Audio", "mrp": 2999.0, "cost_ratio": 0.50, "base_stock": 300, "lead_time": 5, "restock_cost": 20000.0, "base_views": 2400},
        {"name": "Smart Fitness Watch 1.83 inch", "brand": "FitVibe", "cat": "Electronics", "subcat": "Wearables", "mrp": 3499.0, "cost_ratio": 0.48, "base_stock": 250, "lead_time": 7, "restock_cost": 22000.0, "base_views": 2100},
        {"name": "GPS Smartwatch with AMOLED Display", "brand": "FitVibe", "cat": "Electronics", "subcat": "Wearables", "mrp": 7999.0, "cost_ratio": 0.54, "base_stock": 120, "lead_time": 9, "restock_cost": 35000.0, "base_views": 1100},
        {"name": "20000mAh 22.5W Fast Charging Power Bank", "brand": "VoltMax", "cat": "Electronics", "subcat": "Power", "mrp": 1999.0, "cost_ratio": 0.58, "base_stock": 350, "lead_time": 5, "restock_cost": 18000.0, "base_views": 2200},
        {"name": "10000mAh Slim Pocket Power Bank", "brand": "VoltMax", "cat": "Electronics", "subcat": "Power", "mrp": 1299.0, "cost_ratio": 0.60, "base_stock": 400, "lead_time": 5, "restock_cost": 14000.0, "base_views": 2000},
        {"name": "RGB Mechanical Gaming Keyboard", "brand": "NexusGear", "cat": "Electronics", "subcat": "Peripherals", "mrp": 3999.0, "cost_ratio": 0.53, "base_stock": 140, "lead_time": 8, "restock_cost": 20000.0, "base_views": 1300},
        {"name": "Wireless Ergonomic Mouse 2.4GHz", "brand": "NexusGear", "cat": "Electronics", "subcat": "Peripherals", "mrp": 1199.0, "cost_ratio": 0.55, "base_stock": 280, "lead_time": 6, "restock_cost": 10000.0, "base_views": 1400},
        {"name": "7-in-1 USB-C Multiport Hub Adapter", "brand": "LinkPro", "cat": "Electronics", "subcat": "Peripherals", "mrp": 2199.0, "cost_ratio": 0.52, "base_stock": 190, "lead_time": 7, "restock_cost": 15000.0, "base_views": 1200},
        {"name": "1080p FHD Streaming Webcam with Mic", "brand": "VisionTech", "cat": "Electronics", "subcat": "Peripherals", "mrp": 2799.0, "cost_ratio": 0.54, "base_stock": 160, "lead_time": 8, "restock_cost": 16000.0, "base_views": 1100},
        {"name": "Dual Band Wi-Fi 6 Smart Router", "brand": "NetSpeed", "cat": "Electronics", "subcat": "Networking", "mrp": 4499.0, "cost_ratio": 0.56, "base_stock": 130, "lead_time": 8, "restock_cost": 24000.0, "base_views": 1000},
        {"name": "Soundbar with Subwoofer 120W", "brand": "AuraAudio", "cat": "Electronics", "subcat": "Audio", "mrp": 8999.0, "cost_ratio": 0.58, "base_stock": 90, "lead_time": 10, "restock_cost": 40000.0, "base_views": 950},
        {"name": "Surge Protector 6-Socket Extension Board", "brand": "VoltMax", "cat": "Electronics", "subcat": "Power", "mrp": 899.0, "cost_ratio": 0.62, "base_stock": 320, "lead_time": 5, "restock_cost": 9000.0, "base_views": 1600},
        {"name": "Smart Security Camera 360 Pan-Tilt", "brand": "VisionTech", "cat": "Electronics", "subcat": "Smart Home", "mrp": 3299.0, "cost_ratio": 0.52, "base_stock": 170, "lead_time": 7, "restock_cost": 21000.0, "base_views": 1400},
        {"name": "Bluetooth Gaming Headset with Boom Mic", "brand": "NexusGear", "cat": "Electronics", "subcat": "Audio", "mrp": 2699.0, "cost_ratio": 0.54, "base_stock": 200, "lead_time": 6, "restock_cost": 17000.0, "base_views": 1700},
        {"name": "Adjustable Aluminum Laptop Stand", "brand": "LinkPro", "cat": "Electronics", "subcat": "Peripherals", "mrp": 1499.0, "cost_ratio": 0.50, "base_stock": 250, "lead_time": 6, "restock_cost": 12000.0, "base_views": 1650},
        {"name": "Digital Voice Recorder 16GB", "brand": "SoundPulse", "cat": "Electronics", "subcat": "Audio", "mrp": 1999.0, "cost_ratio": 0.55, "base_stock": 110, "lead_time": 8, "restock_cost": 12000.0, "base_views": 800},

        # --- 2. Grocery (18 SKUs) ---
        {"name": "Royal Premium Basmati Rice 5kg", "brand": "ShreeBhog", "cat": "Grocery", "subcat": "Staples", "mrp": 750.0, "cost_ratio": 0.76, "base_stock": 450, "lead_time": 3, "restock_cost": 25000.0, "base_views": 2800},
        {"name": "Refined Sunflower Cooking Oil 5L Can", "brand": "AmrutDhara", "cat": "Grocery", "subcat": "Cooking Essentials", "mrp": 890.0, "cost_ratio": 0.80, "base_stock": 400, "lead_time": 3, "restock_cost": 30000.0, "base_views": 3100},
        {"name": "Chakki Fresh Whole Wheat Atta 10kg", "brand": "ShreeBhog", "cat": "Grocery", "subcat": "Staples", "mrp": 480.0, "cost_ratio": 0.78, "base_stock": 500, "lead_time": 2, "restock_cost": 20000.0, "base_views": 3500},
        {"name": "Pure Cow Ghee Bilona Method 1L", "brand": "GirAmrut", "cat": "Grocery", "subcat": "Dairy & Ghee", "mrp": 950.0, "cost_ratio": 0.72, "base_stock": 250, "lead_time": 4, "restock_cost": 22000.0, "base_views": 2200},
        {"name": "Organic Turmeric Powder 500g", "brand": "Spiceland", "cat": "Grocery", "subcat": "Spices", "mrp": 180.0, "cost_ratio": 0.65, "base_stock": 600, "lead_time": 3, "restock_cost": 8000.0, "base_views": 1900},
        {"name": "Authentic Gujarati Garam Masala 200g", "brand": "Spiceland", "cat": "Grocery", "subcat": "Spices", "mrp": 140.0, "cost_ratio": 0.62, "base_stock": 550, "lead_time": 3, "restock_cost": 6500.0, "base_views": 2100},
        {"name": "California Premium Almonds 1kg", "brand": "NutriBites", "cat": "Grocery", "subcat": "Dry Fruits", "mrp": 999.0, "cost_ratio": 0.75, "base_stock": 280, "lead_time": 4, "restock_cost": 26000.0, "base_views": 2300},
        {"name": "Whole Cashews W320 Grade 500g", "brand": "NutriBites", "cat": "Grocery", "subcat": "Dry Fruits", "mrp": 550.0, "cost_ratio": 0.74, "base_stock": 300, "lead_time": 4, "restock_cost": 15000.0, "base_views": 2000},
        {"name": "Organic Honey Wild Blossom 500g", "brand": "GirAmrut", "cat": "Grocery", "subcat": "Sweeteners", "mrp": 320.0, "cost_ratio": 0.68, "base_stock": 350, "lead_time": 4, "restock_cost": 10000.0, "base_views": 1700},
        {"name": "Assam Strong CTC Tea Leaves 1kg", "brand": "ChaiBagh", "cat": "Grocery", "subcat": "Beverages", "mrp": 420.0, "cost_ratio": 0.70, "base_stock": 420, "lead_time": 3, "restock_cost": 16000.0, "base_views": 2600},
        {"name": "Cold Pressed Kachi Ghani Mustard Oil 1L", "brand": "AmrutDhara", "cat": "Grocery", "subcat": "Cooking Essentials", "mrp": 210.0, "cost_ratio": 0.77, "base_stock": 380, "lead_time": 3, "restock_cost": 12000.0, "base_views": 1800},
        {"name": "Toor Dal Unpolished Desi 2kg", "brand": "ShreeBhog", "cat": "Grocery", "subcat": "Staples", "mrp": 360.0, "cost_ratio": 0.79, "base_stock": 480, "lead_time": 3, "restock_cost": 15000.0, "base_views": 2900},
        {"name": "Crispy Methi Khakhra Box 500g", "brand": "SwadGujarat", "cat": "Grocery", "subcat": "Snacks", "mrp": 160.0, "cost_ratio": 0.60, "base_stock": 500, "lead_time": 2, "restock_cost": 7000.0, "base_views": 2700},
        {"name": "Diet Roasted Makhana Pouch 250g", "brand": "NutriBites", "cat": "Grocery", "subcat": "Snacks", "mrp": 299.0, "cost_ratio": 0.64, "base_stock": 320, "lead_time": 4, "restock_cost": 9000.0, "base_views": 1950},
        {"name": "Instant Coffee Granules Jar 200g", "brand": "ChaiBagh", "cat": "Grocery", "subcat": "Beverages", "mrp": 380.0, "cost_ratio": 0.68, "base_stock": 290, "lead_time": 4, "restock_cost": 11000.0, "base_views": 1850},
        {"name": "Organic Jaggery Powder 1kg", "brand": "GirAmrut", "cat": "Grocery", "subcat": "Sweeteners", "mrp": 150.0, "cost_ratio": 0.65, "base_stock": 410, "lead_time": 3, "restock_cost": 6000.0, "base_views": 1600},
        {"name": "Kashmiri Red Chilli Powder 500g", "brand": "Spiceland", "cat": "Grocery", "subcat": "Spices", "mrp": 240.0, "cost_ratio": 0.66, "base_stock": 390, "lead_time": 3, "restock_cost": 9500.0, "base_views": 1750},
        {"name": "Gujarati Farsan Sev Mamra Mix 400g", "brand": "SwadGujarat", "cat": "Grocery", "subcat": "Snacks", "mrp": 120.0, "cost_ratio": 0.58, "base_stock": 600, "lead_time": 2, "restock_cost": 6000.0, "base_views": 3200},

        # --- 3. Fashion (17 SKUs) ---
        {"name": "100% Cotton Bio-Washed Men Casual T-Shirt", "brand": "UrbanTrend", "cat": "Fashion", "subcat": "Men Apparel", "mrp": 899.0, "cost_ratio": 0.40, "base_stock": 350, "lead_time": 5, "restock_cost": 14000.0, "base_views": 2500},
        {"name": "Slim Fit Stretchable Denim Jeans", "brand": "DenimCraft", "cat": "Fashion", "subcat": "Men Apparel", "mrp": 1999.0, "cost_ratio": 0.44, "base_stock": 220, "lead_time": 7, "restock_cost": 20000.0, "base_views": 2100},
        {"name": "Traditional Bandhani Print Cotton Kurti", "brand": "RangGujarat", "cat": "Fashion", "subcat": "Women Ethnic", "mrp": 1299.0, "cost_ratio": 0.38, "base_stock": 280, "lead_time": 6, "restock_cost": 16000.0, "base_views": 2800},
        {"name": "Surat Art Silk Embroidered Saree", "brand": "RangGujarat", "cat": "Fashion", "subcat": "Women Ethnic", "mrp": 2499.0, "cost_ratio": 0.42, "base_stock": 180, "lead_time": 8, "restock_cost": 22000.0, "base_views": 2900},
        {"name": "Men Classic Linen Formal Shirt", "brand": "UrbanTrend", "cat": "Fashion", "subcat": "Men Apparel", "mrp": 1599.0, "cost_ratio": 0.45, "base_stock": 200, "lead_time": 6, "restock_cost": 15000.0, "base_views": 1600},
        {"name": "Women Casual Cotton Palazzos Set", "brand": "RangGujarat", "cat": "Fashion", "subcat": "Women Ethnic", "mrp": 1499.0, "cost_ratio": 0.39, "base_stock": 240, "lead_time": 6, "restock_cost": 16000.0, "base_views": 2200},
        {"name": "Men Cotton Chino Trousers Slim Fit", "brand": "DenimCraft", "cat": "Fashion", "subcat": "Men Apparel", "mrp": 1799.0, "cost_ratio": 0.43, "base_stock": 210, "lead_time": 6, "restock_cost": 17000.0, "base_views": 1500},
        {"name": "Unisex Oversized Graphic Hoodie", "brand": "UrbanTrend", "cat": "Fashion", "subcat": "Winter Wear", "mrp": 2199.0, "cost_ratio": 0.46, "base_stock": 160, "lead_time": 7, "restock_cost": 18000.0, "base_views": 1900},
        {"name": "Women Rayon Anarkali Kurta Set", "brand": "RangGujarat", "cat": "Fashion", "subcat": "Women Ethnic", "mrp": 1899.0, "cost_ratio": 0.40, "base_stock": 200, "lead_time": 7, "restock_cost": 18000.0, "base_views": 2400},
        {"name": "Men Polo Collar Solid T-Shirt", "brand": "UrbanTrend", "cat": "Fashion", "subcat": "Men Apparel", "mrp": 1099.0, "cost_ratio": 0.42, "base_stock": 310, "lead_time": 5, "restock_cost": 14000.0, "base_views": 2000},
        {"name": "Women Denim High Waist Flared Jeans", "brand": "DenimCraft", "cat": "Fashion", "subcat": "Women Western", "mrp": 2099.0, "cost_ratio": 0.45, "base_stock": 190, "lead_time": 7, "restock_cost": 19000.0, "base_views": 1800},
        {"name": "Navratri Special Chaniya Choli Set", "brand": "RangGujarat", "cat": "Fashion", "subcat": "Festive Wear", "mrp": 3999.0, "cost_ratio": 0.40, "base_stock": 150, "lead_time": 8, "restock_cost": 28000.0, "base_views": 3800},
        {"name": "Men Quilted Lightweight Jacket", "brand": "UrbanTrend", "cat": "Fashion", "subcat": "Winter Wear", "mrp": 2799.0, "cost_ratio": 0.47, "base_stock": 140, "lead_time": 8, "restock_cost": 22000.0, "base_views": 1400},
        {"name": "Women Cotton Nightwear Pajama Set", "brand": "CozyWear", "cat": "Fashion", "subcat": "Sleepwear", "mrp": 1199.0, "cost_ratio": 0.38, "base_stock": 270, "lead_time": 5, "restock_cost": 12000.0, "base_views": 1700},
        {"name": "Men Formal Trousers Wrinkle Free", "brand": "DenimCraft", "cat": "Fashion", "subcat": "Men Apparel", "mrp": 1699.0, "cost_ratio": 0.44, "base_stock": 200, "lead_time": 6, "restock_cost": 16000.0, "base_views": 1300},
        {"name": "Women Floral Print Georgette Maxi Dress", "brand": "UrbanTrend", "cat": "Fashion", "subcat": "Women Western", "mrp": 1899.0, "cost_ratio": 0.41, "base_stock": 180, "lead_time": 6, "restock_cost": 16000.0, "base_views": 1950},
        {"name": "Unisex Cotton Track Pants", "brand": "CozyWear", "cat": "Fashion", "subcat": "Activewear", "mrp": 999.0, "cost_ratio": 0.40, "base_stock": 290, "lead_time": 5, "restock_cost": 13000.0, "base_views": 1850},

        # --- 4. Home & Kitchen (17 SKUs) ---
        {"name": "Hard Anodised 3L Pressure Cooker", "brand": "ChefMaster", "cat": "Home & Kitchen", "subcat": "Cookware", "mrp": 1899.0, "cost_ratio": 0.54, "base_stock": 200, "lead_time": 6, "restock_cost": 20000.0, "base_views": 2100},
        {"name": "Non-Stick 3-Piece Dosa Tawa & Pan Set", "brand": "ChefMaster", "cat": "Home & Kitchen", "subcat": "Cookware", "mrp": 2299.0, "cost_ratio": 0.50, "base_stock": 180, "lead_time": 6, "restock_cost": 21000.0, "base_views": 2300},
        {"name": "100% Pure Cotton King Size Bedsheet 300TC", "brand": "HomeComfort", "cat": "Home & Kitchen", "subcat": "Home Furnishing", "mrp": 1499.0, "cost_ratio": 0.46, "base_stock": 260, "lead_time": 5, "restock_cost": 17000.0, "base_views": 2500},
        {"name": "Airtight Plastic Kitchen Storage Container 12pc", "brand": "SmartOrganize", "cat": "Home & Kitchen", "subcat": "Storage", "mrp": 999.0, "cost_ratio": 0.44, "base_stock": 350, "lead_time": 5, "restock_cost": 15000.0, "base_views": 2700},
        {"name": "Heavy Duty 750W Mixer Grinder 3 Jars", "brand": "ChefMaster", "cat": "Home & Kitchen", "subcat": "Appliances", "mrp": 3499.0, "cost_ratio": 0.58, "base_stock": 130, "lead_time": 8, "restock_cost": 26000.0, "base_views": 1900},
        {"name": "1.8L Stainless Steel Electric Kettle", "brand": "ChefMaster", "cat": "Home & Kitchen", "subcat": "Appliances", "mrp": 1199.0, "cost_ratio": 0.52, "base_stock": 280, "lead_time": 5, "restock_cost": 16000.0, "base_views": 2400},
        {"name": "Microfiber Quick Dry Bath Towels 2-Pack", "brand": "HomeComfort", "cat": "Home & Kitchen", "subcat": "Home Furnishing", "mrp": 799.0, "cost_ratio": 0.42, "base_stock": 320, "lead_time": 4, "restock_cost": 12000.0, "base_views": 2000},
        {"name": "Stainless Steel Kitchen Knife Set with Block", "brand": "ChefMaster", "cat": "Home & Kitchen", "subcat": "Cutlery", "mrp": 1299.0, "cost_ratio": 0.48, "base_stock": 210, "lead_time": 6, "restock_cost": 14000.0, "base_views": 1500},
        {"name": "Borosilicate Glass Food Containers 3pc Set", "brand": "SmartOrganize", "cat": "Home & Kitchen", "subcat": "Storage", "mrp": 1399.0, "cost_ratio": 0.50, "base_stock": 220, "lead_time": 6, "restock_cost": 15000.0, "base_views": 1800},
        {"name": "Automatic 1200W Dry Iron Lightweight", "brand": "ChefMaster", "cat": "Home & Kitchen", "subcat": "Appliances", "mrp": 899.0, "cost_ratio": 0.55, "base_stock": 300, "lead_time": 5, "restock_cost": 13000.0, "base_views": 1900},
        {"name": "Wall Mount Foldable Cloth Drying Rack", "brand": "SmartOrganize", "cat": "Home & Kitchen", "subcat": "Utility", "mrp": 1699.0, "cost_ratio": 0.48, "base_stock": 170, "lead_time": 7, "restock_cost": 15000.0, "base_views": 1400},
        {"name": "Blackout Window Curtains 7 Feet Pair", "brand": "HomeComfort", "cat": "Home & Kitchen", "subcat": "Home Furnishing", "mrp": 1299.0, "cost_ratio": 0.45, "base_stock": 230, "lead_time": 6, "restock_cost": 15000.0, "base_views": 1600},
        {"name": "Cast Iron Pre-Seasoned Roti Tawa 10 inch", "brand": "ChefMaster", "cat": "Home & Kitchen", "subcat": "Cookware", "mrp": 1099.0, "cost_ratio": 0.52, "base_stock": 240, "lead_time": 6, "restock_cost": 14000.0, "base_views": 1850},
        {"name": "Handheld Milk Frother & Egg Beater", "brand": "ChefMaster", "cat": "Home & Kitchen", "subcat": "Appliances", "mrp": 499.0, "cost_ratio": 0.42, "base_stock": 400, "lead_time": 4, "restock_cost": 8000.0, "base_views": 2100},
        {"name": "Anti-Skid Memory Foam Bathroom Mat", "brand": "HomeComfort", "cat": "Home & Kitchen", "subcat": "Home Furnishing", "mrp": 599.0, "cost_ratio": 0.40, "base_stock": 360, "lead_time": 4, "restock_cost": 9000.0, "base_views": 1900},
        {"name": "Insulated Stainless Steel Water Bottle 1L", "brand": "SmartOrganize", "cat": "Home & Kitchen", "subcat": "Hydration", "mrp": 849.0, "cost_ratio": 0.48, "base_stock": 310, "lead_time": 5, "restock_cost": 13000.0, "base_views": 2200},
        {"name": "Compact Spice Box Masala Dani Stainless Steel", "brand": "SmartOrganize", "cat": "Home & Kitchen", "subcat": "Storage", "mrp": 699.0, "cost_ratio": 0.46, "base_stock": 290, "lead_time": 5, "restock_cost": 10000.0, "base_views": 1750},

        # --- 5. Personal Care (15 SKUs) ---
        {"name": "Anti-Dandruff Tea Tree Shampoo 400ml", "brand": "DermaPure", "cat": "Personal Care", "subcat": "Hair Care", "mrp": 499.0, "cost_ratio": 0.45, "base_stock": 380, "lead_time": 4, "restock_cost": 12000.0, "base_views": 2200},
        {"name": "Vitamin C Radiance Face Wash 150ml", "brand": "GlowEssence", "cat": "Personal Care", "subcat": "Skin Care", "mrp": 349.0, "cost_ratio": 0.42, "base_stock": 420, "lead_time": 4, "restock_cost": 10000.0, "base_views": 2600},
        {"name": "Sunscreen Gel SPF 50 PA++++ 50g", "brand": "DermaPure", "cat": "Personal Care", "subcat": "Skin Care", "mrp": 599.0, "cost_ratio": 0.44, "base_stock": 450, "lead_time": 4, "restock_cost": 14000.0, "base_views": 3200},
        {"name": "Cordless Waterproof Beard Trimmer", "brand": "GroomPro", "cat": "Personal Care", "subcat": "Grooming Tools", "mrp": 1499.0, "cost_ratio": 0.52, "base_stock": 200, "lead_time": 6, "restock_cost": 18000.0, "base_views": 2000},
        {"name": "Deep Nourishing Hair Conditioner 250ml", "brand": "DermaPure", "cat": "Personal Care", "subcat": "Hair Care", "mrp": 399.0, "cost_ratio": 0.43, "base_stock": 340, "lead_time": 4, "restock_cost": 9500.0, "base_views": 1800},
        {"name": "Hyaluronic Acid Hydrating Face Serum 30ml", "brand": "GlowEssence", "cat": "Personal Care", "subcat": "Skin Care", "mrp": 699.0, "cost_ratio": 0.40, "base_stock": 300, "lead_time": 5, "restock_cost": 13000.0, "base_views": 2500},
        {"name": "Niacinamide & Zinc Acne Spot Gel 20g", "brand": "DermaPure", "cat": "Personal Care", "subcat": "Skin Care", "mrp": 449.0, "cost_ratio": 0.38, "base_stock": 360, "lead_time": 4, "restock_cost": 10500.0, "base_views": 2300},
        {"name": "Onion Black Seed Hair Oil 200ml", "brand": "GlowEssence", "cat": "Personal Care", "subcat": "Hair Care", "mrp": 429.0, "cost_ratio": 0.46, "base_stock": 350, "lead_time": 4, "restock_cost": 11000.0, "base_views": 2100},
        {"name": "Gentle Exfoliating Coffee Body Scrub 200g", "brand": "GlowEssence", "cat": "Personal Care", "subcat": "Body Care", "mrp": 499.0, "cost_ratio": 0.42, "base_stock": 280, "lead_time": 4, "restock_cost": 9000.0, "base_views": 1700},
        {"name": "Ultrasonic Electric Toothbrush Rechargeable", "brand": "GroomPro", "cat": "Personal Care", "subcat": "Oral Care", "mrp": 1299.0, "cost_ratio": 0.50, "base_stock": 220, "lead_time": 6, "restock_cost": 16000.0, "base_views": 1500},
        {"name": "Aloe Vera Soothing Gel 300ml", "brand": "GlowEssence", "cat": "Personal Care", "subcat": "Skin Care", "mrp": 299.0, "cost_ratio": 0.38, "base_stock": 480, "lead_time": 3, "restock_cost": 9000.0, "base_views": 2400},
        {"name": "Long Lasting Luxury Perfume Spray 100ml", "brand": "AromaLuxe", "cat": "Personal Care", "subcat": "Fragrance", "mrp": 1299.0, "cost_ratio": 0.35, "base_stock": 240, "lead_time": 5, "restock_cost": 14000.0, "base_views": 2100},
        {"name": "Moisturizing Cocoa Butter Body Lotion 400ml", "brand": "DermaPure", "cat": "Personal Care", "subcat": "Body Care", "mrp": 379.0, "cost_ratio": 0.44, "base_stock": 360, "lead_time": 4, "restock_cost": 10000.0, "base_views": 1900},
        {"name": "Natural Charcoal Peel Off Face Mask 100g", "brand": "GlowEssence", "cat": "Personal Care", "subcat": "Skin Care", "mrp": 349.0, "cost_ratio": 0.40, "base_stock": 330, "lead_time": 4, "restock_cost": 8500.0, "base_views": 1850},
        {"name": "Ionic Hair Dryer 1800W Quick Dry", "brand": "GroomPro", "cat": "Personal Care", "subcat": "Grooming Tools", "mrp": 1799.0, "cost_ratio": 0.52, "base_stock": 170, "lead_time": 6, "restock_cost": 18000.0, "base_views": 1600},

        # --- 6. Mobile Accessories (15 SKUs) ---
        {"name": "Military Grade Shockproof Armor Phone Case", "brand": "ArmorGuard", "cat": "Mobile Accessories", "subcat": "Protection", "mrp": 699.0, "cost_ratio": 0.35, "base_stock": 500, "lead_time": 4, "restock_cost": 12000.0, "base_views": 3200},
        {"name": "65W GaN Type-C Fast Charger Adapter", "brand": "VoltMax", "cat": "Mobile Accessories", "subcat": "Charging", "mrp": 1799.0, "cost_ratio": 0.50, "base_stock": 240, "lead_time": 6, "restock_cost": 21000.0, "base_views": 2500},
        {"name": "9H Hardness Edge-to-Edge Tempered Glass 2-Pack", "brand": "ArmorGuard", "cat": "Mobile Accessories", "subcat": "Protection", "mrp": 399.0, "cost_ratio": 0.30, "base_stock": 600, "lead_time": 3, "restock_cost": 9000.0, "base_views": 3800},
        {"name": "Braided Nylon 100W Type-C to Type-C Cable 2M", "brand": "VoltMax", "cat": "Mobile Accessories", "subcat": "Cables", "mrp": 499.0, "cost_ratio": 0.38, "base_stock": 450, "lead_time": 4, "restock_cost": 11000.0, "base_views": 2700},
        {"name": "Magnetic 360 Rotation Car Dashboard Mount", "brand": "LinkPro", "cat": "Mobile Accessories", "subcat": "Mounts & Stands", "mrp": 799.0, "cost_ratio": 0.42, "base_stock": 310, "lead_time": 5, "restock_cost": 13000.0, "base_views": 2000},
        {"name": "15W Qi Fast Wireless Charging Pad", "brand": "VoltMax", "cat": "Mobile Accessories", "subcat": "Charging", "mrp": 1299.0, "cost_ratio": 0.48, "base_stock": 220, "lead_time": 6, "restock_cost": 15000.0, "base_views": 1800},
        {"name": "Camera Lens Protector Ring Aluminum 3pc", "brand": "ArmorGuard", "cat": "Mobile Accessories", "subcat": "Protection", "mrp": 299.0, "cost_ratio": 0.32, "base_stock": 550, "lead_time": 3, "restock_cost": 7500.0, "base_views": 2600},
        {"name": "Foldable Desktop Mobile & Tablet Stand", "brand": "LinkPro", "cat": "Mobile Accessories", "subcat": "Mounts & Stands", "mrp": 449.0, "cost_ratio": 0.38, "base_stock": 380, "lead_time": 4, "restock_cost": 9000.0, "base_views": 2200},
        {"name": "Bluetooth Remote Selfie Stick with Tripod", "brand": "LinkPro", "cat": "Mobile Accessories", "subcat": "Photography", "mrp": 999.0, "cost_ratio": 0.44, "base_stock": 260, "lead_time": 5, "restock_cost": 14000.0, "base_views": 1900},
        {"name": "Type-C to 3.5mm DAC Audio Adapter", "brand": "AuraAudio", "cat": "Mobile Accessories", "subcat": "Adapters", "mrp": 599.0, "cost_ratio": 0.40, "base_stock": 340, "lead_time": 4, "restock_cost": 9500.0, "base_views": 1700},
        {"name": "Waterproof Bike Mobile Phone Holder", "brand": "ArmorGuard", "cat": "Mobile Accessories", "subcat": "Mounts & Stands", "mrp": 699.0, "cost_ratio": 0.42, "base_stock": 280, "lead_time": 5, "restock_cost": 11000.0, "base_views": 1850},
        {"name": "30W Dual Port Fast Car Charger", "brand": "VoltMax", "cat": "Mobile Accessories", "subcat": "Charging", "mrp": 849.0, "cost_ratio": 0.46, "base_stock": 300, "lead_time": 5, "restock_cost": 13000.0, "base_views": 2100},
        {"name": "Silicone Liquid Soft Case for iPhone/Galaxy", "brand": "ArmorGuard", "cat": "Mobile Accessories", "subcat": "Protection", "mrp": 499.0, "cost_ratio": 0.34, "base_stock": 420, "lead_time": 4, "restock_cost": 10000.0, "base_views": 2900},
        {"name": "L-Shape Gaming Lightning Cable 1.5M", "brand": "NexusGear", "cat": "Mobile Accessories", "subcat": "Cables", "mrp": 449.0, "cost_ratio": 0.38, "base_stock": 360, "lead_time": 4, "restock_cost": 9000.0, "base_views": 1600},
        {"name": "Micro-SD Card 128GB UHS-I U3 High Speed", "brand": "VisionTech", "cat": "Mobile Accessories", "subcat": "Storage", "mrp": 1199.0, "cost_ratio": 0.55, "base_stock": 270, "lead_time": 5, "restock_cost": 18000.0, "base_views": 2300},

        # --- 7. Footwear (15 SKUs) ---
        {"name": "Men Lightweight Breathable Running Shoes", "brand": "AeroStride", "cat": "Footwear", "subcat": "Men Sports", "mrp": 2499.0, "cost_ratio": 0.46, "base_stock": 240, "lead_time": 6, "restock_cost": 25000.0, "base_views": 2700},
        {"name": "Men Genuine Leather Slip-On Formal Shoes", "brand": "RoyalStep", "cat": "Footwear", "subcat": "Men Formal", "mrp": 3299.0, "cost_ratio": 0.48, "base_stock": 160, "lead_time": 7, "restock_cost": 24000.0, "base_views": 1700},
        {"name": "Women Comfort Walking Memory Foam Sneakers", "brand": "AeroStride", "cat": "Footwear", "subcat": "Women Casual", "mrp": 2199.0, "cost_ratio": 0.44, "base_stock": 250, "lead_time": 6, "restock_cost": 22000.0, "base_views": 2600},
        {"name": "Orthopedic Soft Cushion Daily Slippers", "brand": "ComfortWalk", "cat": "Footwear", "subcat": "Daily Wear", "mrp": 799.0, "cost_ratio": 0.38, "base_stock": 420, "lead_time": 4, "restock_cost": 12000.0, "base_views": 3100},
        {"name": "Men Casual Canvas Loafers", "brand": "RoyalStep", "cat": "Footwear", "subcat": "Men Casual", "mrp": 1499.0, "cost_ratio": 0.42, "base_stock": 280, "lead_time": 5, "restock_cost": 17000.0, "base_views": 2100},
        {"name": "Women Strappy Block Heel Party Sandals", "brand": "GlamourStep", "cat": "Footwear", "subcat": "Women Party", "mrp": 1899.0, "cost_ratio": 0.40, "base_stock": 200, "lead_time": 6, "restock_cost": 17000.0, "base_views": 2300},
        {"name": "Unisex Waterproof Outdoor Hiking Trekking Shoes", "brand": "AeroStride", "cat": "Footwear", "subcat": "Outdoor", "mrp": 3799.0, "cost_ratio": 0.50, "base_stock": 140, "lead_time": 8, "restock_cost": 26000.0, "base_views": 1600},
        {"name": "Women Ethnic Traditional Mojari Jutti", "brand": "GlamourStep", "cat": "Footwear", "subcat": "Ethnic", "mrp": 1199.0, "cost_ratio": 0.36, "base_stock": 290, "lead_time": 5, "restock_cost": 12000.0, "base_views": 2800},
        {"name": "Men Leather Classic Derby Lace-Up Shoes", "brand": "RoyalStep", "cat": "Footwear", "subcat": "Men Formal", "mrp": 3499.0, "cost_ratio": 0.48, "base_stock": 150, "lead_time": 7, "restock_cost": 24000.0, "base_views": 1500},
        {"name": "Men Rugged Outdoor Sports Floater Sandals", "brand": "ComfortWalk", "cat": "Footwear", "subcat": "Men Casual", "mrp": 1299.0, "cost_ratio": 0.42, "base_stock": 310, "lead_time": 5, "restock_cost": 15000.0, "base_views": 2400},
        {"name": "Women Flat Pointed-Toe Ballerina Bellies", "brand": "GlamourStep", "cat": "Footwear", "subcat": "Women Casual", "mrp": 999.0, "cost_ratio": 0.38, "base_stock": 330, "lead_time": 5, "restock_cost": 13000.0, "base_views": 2200},
        {"name": "Men High-Top Basketball Street Sneakers", "brand": "AeroStride", "cat": "Footwear", "subcat": "Men Sports", "mrp": 2999.0, "cost_ratio": 0.46, "base_stock": 170, "lead_time": 7, "restock_cost": 23000.0, "base_views": 1900},
        {"name": "Extra Soft Anti-Skid Indoor Bathroom Slides", "brand": "ComfortWalk", "cat": "Footwear", "subcat": "Daily Wear", "mrp": 499.0, "cost_ratio": 0.35, "base_stock": 480, "lead_time": 4, "restock_cost": 8500.0, "base_views": 2700},
        {"name": "Women Chunky Platform Casual Sneakers", "brand": "GlamourStep", "cat": "Footwear", "subcat": "Women Casual", "mrp": 2399.0, "cost_ratio": 0.44, "base_stock": 210, "lead_time": 6, "restock_cost": 20000.0, "base_views": 2500},
        {"name": "Men Pure Leather Kolhapuri Chappal", "brand": "RoyalStep", "cat": "Footwear", "subcat": "Ethnic", "mrp": 1399.0, "cost_ratio": 0.40, "base_stock": 230, "lead_time": 5, "restock_cost": 13000.0, "base_views": 1800},

        # --- 8. Sports & Fitness (15 SKUs) ---
        {"name": "High Density Anti-Slip Yoga Mat 6mm", "brand": "FlexFit", "cat": "Sports & Fitness", "subcat": "Yoga & Pilates", "mrp": 999.0, "cost_ratio": 0.44, "base_stock": 320, "lead_time": 5, "restock_cost": 14000.0, "base_views": 2600},
        {"name": "Solid Hex Rubber Encased Dumbbells 5kg Pair", "brand": "IronCore", "cat": "Sports & Fitness", "subcat": "Strength Training", "mrp": 1899.0, "cost_ratio": 0.52, "base_stock": 190, "lead_time": 7, "restock_cost": 21000.0, "base_views": 2000},
        {"name": "Heavy Duty Loop Resistance Bands 5-Pack", "brand": "FlexFit", "cat": "Sports & Fitness", "subcat": "Fitness Accessories", "mrp": 799.0, "cost_ratio": 0.38, "base_stock": 380, "lead_time": 4, "restock_cost": 11000.0, "base_views": 2400},
        {"name": "Steel Ball Bearing Speed Skipping Rope", "brand": "FlexFit", "cat": "Sports & Fitness", "subcat": "Cardio", "mrp": 449.0, "cost_ratio": 0.36, "base_stock": 450, "lead_time": 4, "restock_cost": 8000.0, "base_views": 2500},
        {"name": "Stainless Steel Protein Shaker Bottle 700ml", "brand": "NutriBites", "cat": "Sports & Fitness", "subcat": "Hydration & Diet", "mrp": 699.0, "cost_ratio": 0.42, "base_stock": 340, "lead_time": 4, "restock_cost": 10000.0, "base_views": 2100},
        {"name": "Adjustable Doorway Pull-Up Chin-Up Bar", "brand": "IronCore", "cat": "Sports & Fitness", "subcat": "Strength Training", "mrp": 1499.0, "cost_ratio": 0.50, "base_stock": 200, "lead_time": 6, "restock_cost": 16000.0, "base_views": 1700},
        {"name": "Double Wheel Ab Roller with Knee Mat", "brand": "FlexFit", "cat": "Sports & Fitness", "subcat": "Core Training", "mrp": 649.0, "cost_ratio": 0.40, "base_stock": 310, "lead_time": 5, "restock_cost": 9000.0, "base_views": 1900},
        {"name": "Gym Weight Lifting Gloves with Wrist Wrap", "brand": "IronCore", "cat": "Sports & Fitness", "subcat": "Fitness Accessories", "mrp": 599.0, "cost_ratio": 0.38, "base_stock": 360, "lead_time": 4, "restock_cost": 9500.0, "base_views": 1850},
        {"name": "Graphite Badminton Racket Twin Pack with Cover", "brand": "AeroStride", "cat": "Sports & Fitness", "subcat": "Racquet Sports", "mrp": 1999.0, "cost_ratio": 0.46, "base_stock": 210, "lead_time": 6, "restock_cost": 18000.0, "base_views": 2200},
        {"name": "Official Size Match Football TPU Cover", "brand": "IronCore", "cat": "Sports & Fitness", "subcat": "Team Sports", "mrp": 899.0, "cost_ratio": 0.42, "base_stock": 280, "lead_time": 5, "restock_cost": 11000.0, "base_views": 1950},
        {"name": "Adjustable Ankle & Wrist Weights 2kg Pair", "brand": "FlexFit", "cat": "Sports & Fitness", "subcat": "Strength Training", "mrp": 949.0, "cost_ratio": 0.44, "base_stock": 260, "lead_time": 5, "restock_cost": 12000.0, "base_views": 1600},
        {"name": "Deep Tissue Muscle Foam Roller 18 inch", "brand": "FlexFit", "cat": "Sports & Fitness", "subcat": "Recovery", "mrp": 1099.0, "cost_ratio": 0.45, "base_stock": 220, "lead_time": 5, "restock_cost": 12000.0, "base_views": 1750},
        {"name": "Knee Support Compression Sleeve 2-Pack", "brand": "FlexFit", "cat": "Sports & Fitness", "subcat": "Supports", "mrp": 699.0, "cost_ratio": 0.36, "base_stock": 390, "lead_time": 4, "restock_cost": 9000.0, "base_views": 2300},
        {"name": "Durable Water Resistant Gym Duffel Bag", "brand": "UrbanTrend", "cat": "Sports & Fitness", "subcat": "Bags", "mrp": 1399.0, "cost_ratio": 0.42, "base_stock": 240, "lead_time": 5, "restock_cost": 14000.0, "base_views": 2000},
        {"name": "Push-Up Stand Bars with Cushioned Grips", "brand": "IronCore", "cat": "Sports & Fitness", "subcat": "Strength Training", "mrp": 549.0, "cost_ratio": 0.38, "base_stock": 350, "lead_time": 4, "restock_cost": 8500.0, "base_views": 1800}
    ]

    assert len(raw_products) == 130, f"Expected 130 products, got {len(raw_products)}"

    # Assign cohorts sequentially to distribute categories evenly across time
    # Sort or interleave products so each cohort gets an even mix of categories
    products_by_category = {}
    for p in raw_products:
        cat = p["cat"]
        products_by_category.setdefault(cat, []).append(p)

    interleaved_products = []
    max_cat_len = max(len(v) for v in products_by_category.values())
    for i in range(max_cat_len):
        for cat in sorted(products_by_category.keys()):
            if i < len(products_by_category[cat]):
                interleaved_products.append(products_by_category[cat][i])

    # Assign to 9 cohorts based on COHORT_SCHEDULE counts
    assigned_products = []
    idx = 0
    sku_counter = 1

    for cohort in COHORT_SCHEDULE:
        cohort_id = cohort["cohort_id"]
        launch_date = cohort["launch_date"]
        count = cohort["sku_count"]

        cohort_batch = interleaved_products[idx : idx + count]
        idx += count

        for p in cohort_batch:
            cat_code = p["cat"][:4].upper()
            prod_id = f"PROD-{cat_code}-{sku_counter:03d}"
            sku_code = f"SKU-{cat_code}-{sku_counter:03d}"
            sku_counter += 1

            mrp = float(p["mrp"])
            cost_price = round(mrp * p["cost_ratio"], 2)
            min_price = round(max(cost_price * 1.055, mrp * 0.60), 2)  # Strict 5.5% margin floor
            max_price = round(mrp * 1.05, 2)

            assigned_products.append({
                "Product_ID": prod_id,
                "Product_Name": p["name"],
                "Brand": p["brand"],
                "Category": p["cat"],
                "Subcategory": p["subcat"],
                "SKU": sku_code,
                "Base_MRP": mrp,
                "Cost_Price": cost_price,
                "Min_Allowed_Price": min_price,
                "Max_Allowed_Price": max_price,
                "Base_Stock_Level": p["base_stock"],
                "Reorder_Point": max(25, int(p["base_stock"] * 0.25)),
                "Lead_Time_Days": p["lead_time"],
                "Restock_Cost": p["restock_cost"],
                "Base_Views": p["base_views"],
                "Cohort_ID": cohort_id,
                "Launch_Date": launch_date
            })

    return assigned_products

if __name__ == "__main__":
    catalog = build_product_catalog()
    print(f"Catalog generated successfully with {len(catalog)} SKUs.")
