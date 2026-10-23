# THỐNG KÊ BỘ DỮ LIỆU

## 1. Tổng quan

Bộ dữ liệu được xây dựng để phục vụ đề tài “Khung bảo vệ dữ liệu cho trợ lý trí tuệ nhân tạo dùng trong nhà trường”.

Tổng cộng có 50 tài liệu văn bản định dạng `.txt`, được phân thành ba mức bảo mật.

## 2. Thống kê theo mức phân loại

| Mức phân loại | Số lượng | Tỷ lệ |
|---|---:|---:|
| Public | 20 | 40% |
| Internal | 18 | 36% |
| Restricted | 12 | 24% |
| **Tổng** | **50** | **100%** |

## 3. Phân quyền truy cập

| Vai trò | Public | Internal | Restricted |
|---|---|---|---|
| SinhVien | Được phép | Không | Không |
| GiangVien | Được phép | Được phép | Không |
| QuanTri | Được phép | Được phép | Được phép |

## 4. Nguồn dữ liệu

Bộ dữ liệu sử dụng nguồn tham khảo công khai từ các trường đại học Việt Nam, bao gồm:

- Trường Đại học Giao thông vận tải TP.HCM.
- Trường Đại học Mở TP.HCM.
- Trường Đại học Khoa học Tự nhiên – ĐHQG-HCM.
- Trường Đại học Thủ Dầu Một.

Trong đó:

- 20 tài liệu Public được diễn giải từ nguồn công khai.
- 18 tài liệu Internal là tình huống nội bộ giả lập.
- 12 tài liệu Restricted là hồ sơ hạn chế giả lập.

## 5. Đặc điểm dữ liệu

- Định dạng nội dung: TXT.
- Định dạng metadata: JSON và CSV.
- Độ dài thiết kế: 150–400 từ/tài liệu.
- Mỗi tài liệu có mã định danh riêng.
- Mỗi tài liệu được gán mức phân loại và danh sách vai trò truy cập.
- Không sử dụng dữ liệu cá nhân thật.

## 6. Mục đích sử dụng

Bộ dữ liệu phục vụ các hoạt động:

1. Kiểm thử xác thực và phân quyền theo vai trò.
2. Kiểm thử kiểm soát truy xuất tài liệu trước khi đưa vào RAG.
3. Kiểm thử khả năng ngăn truy cập tài liệu trái phép.
4. Kiểm thử lọc thông tin nhạy cảm trong câu trả lời.
5. Ghi nhận kết quả và đánh giá hiệu quả của các cơ chế bảo vệ.