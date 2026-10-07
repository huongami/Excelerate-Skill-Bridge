UI cần làm lại hoàn toàn.

Làm mới UI theo thiết kế trong skill/design/design.md

sử dụng skill https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git

sản phẩm này cần có 3 thành phần

landing homepage có chức năng giới thiệu product và sign in/sign up

sign up có chức năng upload CV, sau đó scan CV thành thông tin cá nhân và thông tin skill

đăng ký cần có tick đồng ý với term và điều kiện (nhấn vào sẽ hiện ra pop up để đọc, ghi nội dung cho tôi)

nếu người dùng không muốn upload CV khi sign up thì đăng nhập bằng Google Mail (chỉ làm protocol) sau đó homepage sẽ có button + để Upload CV

Sau khi user đăng nhập và đã có CV để extract thông tin về kinh nghiệm, kỹ năng, alias để hiển thị với HR

trang chủ hiển thị search bar, phía dưới hiển thị danh sách các job theo độ thích hợp

mỗi job cần có các thông tin sau:
điểm overall
mô tả ngắn gọn về job
mức độ phù hợp (% match dựa trên ANZSCO)
mức độ skill gap
thời gian đăng (ví dụ đăng 13 ngày trước)

khi người dùng nhấn vào thì sẽ ra thông tin chi tiết, line chart cho % match và line chart cho skill gap cùng diễn giải chi tiết

2 nút là Apply hoặc Ignore

ngoài ra mỗi phần hiển thị job sẽ đều có nút save để vào danh sách yêu thích và nút report để báo cáo job hiển thị sai (cần hiện thực chi tiết behavior của các nút này chứ không chỉ làm cho có)

thứ tự hiển thị sẽ được quyết định dựa trên thuật toán ưu tiên job mà trước đó đã hiện thực. Bổ sung tính năng theo dõi action thêm vào yêu thích hay nhấn ignore để quyết định rank của job

nếu nhấn nút apply thì process quá trình gửi CV cho HR. Nếu nhấn Ignore thì xoá khỏi danh sách hiển thị

ở rìa trái màn hình sẽ là menu cho user gồm icon account để sửa thông tin cá nhân, sửa CV, update skill, chỉnh skill mà AI ghi nếu AI sai. Cùng với đó là danh sách job yêu thích, danh sách job apply

khi nhấn vào danh sách job apply, hiển thị ngắn gọn tên Job, công ty status các job (reviewd, CV scanning, interview...), Khi nhấn vào thì hiện ra timeline bar để xem status hiện tại đang ở đâu với toàn bộ quá trình apply đến lúc nhận việc (tự ghi các checkpoint cho phù hợp)

Ngoài ra thêm tính năng so sánh job với mỗi job sẽ được hiển thị theo dạng dashboard kiểm mạng nhện, so sánh các metric chung thì chart các job lồng lên nhau

loại thứ hai là user là HR

với HR thì tương tự cần đăng JD lúc tạo account. Nếu không thêm JD thì homepage hiển thị button để thêm

sau khi thêm thì trang chủ hiển thị dashboard overall cho các job mà họ đã đăng trên platform hiện tại (tổng số job, tổng số active, tổng số hết hạn, tổng số nhận việc, tổng số từ chối)
page tiếp theo hiển thị danh sách các job đã đăng, mỗi job sẽ có các thông tin sau:
Tên job, tên công ty
mô tả job,
thời gian đăng
số lượt xuất hiện, số người xem, số người apply

ở rìa trái màn hình sẽ là menu cho HR gồm icon account để sửa thông tin cá nhân, sửa JD, update chỉnh các ý mà AI ghi nếu AI sai. 

phần rìa trái sẽ còn có danh sách là về candidate
hiển thị alias (do người dùng chọn), title, kinh ngiệm, mức độ phù hợp (% match dựa trên ANZSCO),
mức độ skill gap, điểm overall, status của họ

mỗi phần thông tin sẽ cần hiển thị kiểu thu gọn, nhấn vào mới ra chi tiết

page candidate cũng thêm tính năng so sánh, với mỗi ứng viên sẽ được hiển thị theo dạng dashboard kiểm mạng nhện, so sánh các skill và kinh nghiệm
thì chart mỗi người sẽ lồng lên nhau

thứ hiển thị job, chấm điểm canđiate sẽ lấy từ công thức mà mới build trước đây trong repo này

data cũng có sẵn xong folder data. Xem các data đó là data user (cả người kiếm việc và HR) input vào platform, hãy thực hiện product này để nó hoạt động trơn tru từ phía người tìm việc và cả HR để mô phỏng quá trình tuyển dụng đầy đủ