# Zalo Web Selectors - Hướng dẫn chính xác

## Thông tin cập nhật: 2026-02-12

Các selector này đã được test và hoạt động với cấu trúc Zalo Web hiện tại.

## Quy trình lấy danh sách thành viên

### Bước 1: Click nút xem thông tin nhóm
**Selector:** `main header>div:nth-child(2)>div[icon]`

**Mô tả:** 
- Nút này nằm ở header của trang chat
- Khi click sẽ mở panel thông tin nhóm bên phải

**Fallback selectors (nếu selector chính không hoạt động):**
- `main header div[icon]`
- `header div[class*="info"]`
- `button[class*="info"]`

### Bước 2: Click nút xem thành viên
**Selector:** `aside div[id='sideBodyScrollBox'] >div >div>div>div>div:nth-child(2)>div:last-child`

**Mô tả:**
- Nút này xuất hiện trong panel thông tin nhóm (aside)
- Khi click sẽ hiển thị danh sách đầy đủ thành viên

**Fallback selectors:**
- `aside div[id='sideBodyScrollBox'] div:last-child`
- `div:has-text("Xem thành viên")`
- `div:has-text("thành viên")`

### Bước 3: Lấy tên thành viên
**Selector:** `div[id='member-group'] div[class='chat-box-member__info__name v2']>div`

**Mô tả:**
- Selector này lấy tên của từng thành viên trong danh sách
- Tên có thể chứa `&nbsp;` (non-breaking space), cần replace thành space thông thường
- Ví dụ: "Hải Dì" sẽ hiển thị trong HTML là "Hải&nbsp;Dì"

**Xử lý đặc biệt:**
```javascript
// Lấy innerHTML thay vì innerText để handle &nbsp;
const innerHTML = element.innerHTML;
const name = innerHTML.replace(/&nbsp;/g, ' ').trim();
```

**Fallback selectors:**
- `div[id='member-group'] div[class*='chat-box-member__info__name']>div`
- `div[id='member-group'] div[class*='member__info__name']>div`
- `div[id='member-group'] div[class*='name']`

## Scroll để load thêm thành viên

Danh sách thành viên được load động khi scroll. Cần scroll trong container đúng:

### Container cần scroll
**Primary:** `div[id='member-group']`
**Secondary:** `aside div[id='sideBodyScrollBox']`

**JavaScript để scroll:**
```javascript
// Scroll member group
const memberGroup = document.querySelector("div[id='member-group']");
if (memberGroup) {
    memberGroup.scrollTop = memberGroup.scrollHeight;
}

// Scroll side panel
const scrollBox = document.querySelector("aside div[id='sideBodyScrollBox']");
if (scrollBox) {
    scrollBox.scrollTop = scrollBox.scrollHeight;
}
```

## Lưu ý quan trọng

### 1. Timing
- Sau mỗi click, đợi 2 giây để UI load
- Sau mỗi scroll, đợi 1.5 giây để member mới load

### 2. Xử lý &nbsp;
- Tên thành viên trong HTML dùng `&nbsp;` thay vì khoảng trắng thường
- Phải dùng `innerHTML` hoặc replace `&nbsp;` với space

### 3. Stop condition
- Dừng scroll khi không có thành viên mới sau 5 lần scroll liên tiếp
- Đảm bảo tránh infinite loop

### 4. Error handling
- Luôn có fallback selector
- Log rõ ràng selector nào đang được dùng
- Báo lỗi chi tiết nếu không tìm thấy elements

## Test Selectors

Để test các selector này trong Browser Console:

```javascript
// Test selector nút thông tin nhóm
document.querySelector('main header>div:nth-child(2)>div[icon]')

// Test selector nút xem thành viên
document.querySelector("aside div[id='sideBodyScrollBox'] >div >div>div>div>div:nth-child(2)>div:last-child")

// Test selector tên thành viên
document.querySelectorAll("div[id='member-group'] div[class='chat-box-member__info__name v2']>div")

// Lấy tất cả tên thành viên
Array.from(document.querySelectorAll("div[id='member-group'] div[class='chat-box-member__info__name v2']>div"))
    .map(el => el.innerHTML.replace(/&nbsp;/g, ' ').trim())
```

## Changelog

### v1.0 - 2026-02-12
- Initial selectors documentation
- Tested and verified with current Zalo Web structure
- Added fallback selectors for robustness
- Documented &nbsp; handling requirement
