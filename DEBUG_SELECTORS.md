# Hướng dẫn Debug Selectors cho Zalo Web

## Vấn đề
Nếu ứng dụng không lấy được danh sách thành viên từ nhóm Zalo, có thể do cấu trúc HTML của Zalo Web đã thay đổi và các selector cần được cập nhật.

## Cách debug

### 1. Chạy ứng dụng và xem Debug Info
Khi bạn chạy ứng dụng, nó sẽ hiển thị thông tin debug về cấu trúc trang:
- Số lượng elements tìm thấy với mỗi từ khóa (member, contact, user, name, list, item)
- Ví dụ về các elements được tìm thấy

### 2. Sử dụng Browser Developer Tools
1. Khi browser mở và đã đăng nhập vào nhóm Zalo, **ĐỂ BROWSER MỞ**
2. Nhấn **F12** để mở Developer Tools
3. Chuyển sang tab **Elements** (hoặc **Inspector**)
4. Tìm một tên thành viên trong danh sách
5. Click chuột phải vào tên đó và chọn **Inspect** hoặc **Inspect Element**
6. Xem cấu trúc HTML xung quanh:
   - Tìm class names của element chứa tên
   - Tìm class names của parent elements
   - Ghi chú lại pattern

### 3. Test Selector trong Console
1. Trong Developer Tools, chuyển sang tab **Console**
2. Thử các lệnh sau để test selector:

```javascript
// Test selector cơ bản
document.querySelectorAll('[class*="member"]').length

// Xem nội dung của elements
document.querySelectorAll('[class*="member"]').forEach(el => console.log(el.innerText))

// Thử các selector khác
document.querySelectorAll('div[class*="contact"]').forEach(el => console.log(el.innerText))
document.querySelectorAll('div[class*="user"]').forEach(el => console.log(el.innerText))
document.querySelectorAll('span[class*="name"]').forEach(el => console.log(el.innerText))
```

### 4. Cập nhật Selectors
Sau khi tìm được selector đúng, cập nhật file `src/scraper/zalo_scraper.py`:

```python
# Trong method scrape_members, tìm dòng:
possible_selectors = [
    # Thêm selector của bạn vào đầu list
    'YOUR_SELECTOR_HERE',
    'div[class*="MemberItem"]',
    # ... các selector khác
]
```

### 5. Các Pattern thường gặp

#### Pattern 1: List item với class cụ thể
```javascript
// HTML: <div class="member-item"><span>Tên người dùng</span></div>
selector = 'div.member-item span'
```

#### Pattern 2: Attribute data
```javascript
// HTML: <div data-type="member" data-name="Tên">...</div>
selector = '[data-type="member"]'
// Lấy tên từ attribute: element.getAttribute('data-name')
```

#### Pattern 3: Nested structure
```javascript
// HTML: <ul class="member-list"><li><div class="user-info"><p>Tên</p></div></li></ul>
selector = 'ul.member-list li .user-info p'
```

## Ví dụ thực tế

### Nếu HTML của Zalo Web là:
```html
<div class="conv-member-list">
  <div class="member-item" data-id="123">
    <div class="avatar">...</div>
    <div class="member-name">Nguyễn Văn A</div>
  </div>
  <div class="member-item" data-id="124">
    <div class="avatar">...</div>
    <div class="member-name">Trần Thị B</div>
  </div>
</div>
```

### Selector nên dùng:
```python
selector = 'div.member-item .member-name'
# hoặc
selector = 'div[class*="member-item"] div[class*="member-name"]'
```

## Mẹo

1. **Dùng `[class*="keyword"]`** thay vì `.exact-class` để tránh lỗi khi class có thêm số hoặc suffix
2. **Test nhiều selector** - thêm nhiều selector vào list, code sẽ thử từng cái
3. **Kiểm tra scroll** - đảm bảo danh sách thành viên có thể scroll được
4. **Đợi loading** - một số element có thể load chậm, cần đợi thêm

## Liên hệ
Nếu vẫn không giải quyết được, hãy:
1. Chụp ảnh màn hình HTML structure (F12 → Elements tab)
2. Copy HTML của một thành viên (right-click → Copy → Copy outerHTML)
3. Gửi thông tin để được hỗ trợ
