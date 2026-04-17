/**
 * ZALO WEB MEMBER SCRAPER HELPER
 * 
 * Hướng dẫn sử dụng:
 * 1. Mở Zalo Web và đăng nhập
 * 2. Vào nhóm cần lấy danh sách thành viên
 * 3. Nhấn F12 để mở Developer Console
 * 4. Copy toàn bộ code này và paste vào Console
 * 5. Nhấn Enter để chạy
 * 6. Xem kết quả và copy selector phù hợp
 */

console.log("=== ZALO WEB MEMBER SCRAPER HELPER ===\n");

// Test các selector phổ biến
const testSelectors = [
    // Zalo-specific patterns
    'div[class*="MemberItem"]',
    'div[class*="member-item"]',
    'div[class*="ContactItem"]',
    'div[class*="contact-item"]',
    'li[class*="member"]',
    'div[class*="UserItem"]',
    'div[class*="user-item"]',
    // Generic patterns
    '[data-id*="member"]',
    'div[class*="member"]',
    'div[class*="contact"]',
    'div[class*="user"]',
    'span[class*="name"]',
    'div[class*="name"]',
    'p[class*="name"]',
    // Nested patterns
    'div[class*="member"] span[class*="name"]',
    'div[class*="contact"] span[class*="name"]',
    'div[class*="list"] > div > div'
];

console.log("Testing selectors...\n");

const results = [];

testSelectors.forEach(selector => {
    try {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
            // Get sample text
            const samples = [];
            for (let i = 0; i < Math.min(3, elements.length); i++) {
                const text = elements[i].innerText ? elements[i].innerText.trim() : '';
                if (text) {
                    samples.push(text.substring(0, 50));
                }
            }
            
            if (samples.length > 0) {
                results.push({
                    selector: selector,
                    count: elements.length,
                    samples: samples
                });
            }
        }
    } catch (e) {
        // Skip invalid selectors
    }
});

// Sort by count (descending)
results.sort((a, b) => b.count - a.count);

console.log("Found " + results.length + " working selectors:\n");

results.forEach((result, index) => {
    console.log(`${index + 1}. Selector: "${result.selector}"`);
    console.log(`   Elements found: ${result.count}`);
    console.log(`   Sample texts:`);
    result.samples.forEach((sample, i) => {
        console.log(`     ${i + 1}. "${sample}"`);
    });
    console.log("");
});

// Try to extract all unique names
console.log("\n=== ATTEMPTING TO EXTRACT ALL NAMES ===\n");

const allNames = new Set();
const keywords = ['member', 'contact', 'user', 'name'];

keywords.forEach(keyword => {
    const elements = document.querySelectorAll(`[class*="${keyword}"]`);
    elements.forEach(el => {
        const text = el.innerText ? el.innerText.trim() : '';
        if (text && text.length >= 2 && text.length <= 100) {
            // Only add if contains letters
            if (/[a-zA-ZÀ-ỹ\u00C0-\u024F\u1E00-\u1EFF]/.test(text)) {
                // Split by newlines to handle multi-line elements
                const lines = text.split('\n');
                lines.forEach(line => {
                    const cleaned = line.trim();
                    if (cleaned.length >= 2 && cleaned.length <= 100) {
                        allNames.add(cleaned);
                    }
                });
            }
        }
    });
});

console.log(`Total unique names/texts found: ${allNames.size}`);
console.log("\nFirst 20 names:");
Array.from(allNames).slice(0, 20).forEach((name, i) => {
    console.log(`  ${i + 1}. ${name}`);
});

// Provide recommendation
console.log("\n=== RECOMMENDATION ===\n");
if (results.length > 0) {
    const best = results[0];
    console.log(`Best selector appears to be:`);
    console.log(`"${best.selector}"`);
    console.log(`\nTo use this selector, update src/scraper/zalo_scraper.py:`);
    console.log(`Add this line at the beginning of possible_selectors list:`);
    console.log(`    '${best.selector}',`);
} else {
    console.log("No good selectors found automatically.");
    console.log("Please manually inspect the HTML structure:");
    console.log("1. Right-click on a member name");
    console.log("2. Select 'Inspect' or 'Inspect Element'");
    console.log("3. Look at the class names and structure");
    console.log("4. Update the selector in src/scraper/zalo_scraper.py");
}

console.log("\n=== EXPORT DATA ===\n");
console.log("To export all found names, run:");
console.log("copy(Array.from(allNames))");
console.log("\nThen paste into a text editor to save.");
