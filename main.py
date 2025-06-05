from flask import Flask, request, render_template, send_file
import pandas as pd
import os
import zipfile
from datetime import datetime
from unidecode import unidecode

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Hàm hỗ trợ
def assign_khoa(ma_nganh):
    if pd.isnull(ma_nganh):
        return None
    elif ('7480201' in ma_nganh or '7480103' in ma_nganh or '7480107' in ma_nganh):
        return 'Khoa Công nghệ thông tin'
    elif ('7510301' in ma_nganh or '7510205' in ma_nganh or '7510202' in ma_nganh or '7510103' in ma_nganh):
        return 'Khoa Kỹ thuật'
    elif ('7540101' in ma_nganh or '7510406' in ma_nganh or '7510401' in ma_nganh or '7420201' in ma_nganh or '7720301' in ma_nganh or '7720601' in ma_nganh):
        return 'Khoa Công nghệ'
    elif ('7320104' in ma_nganh or '7210403' in ma_nganh or '7210408' in ma_nganh):
        return 'Khoa Truyền thông - Thiết kế'
    elif ('7340101' in ma_nganh or '7810103' in ma_nganh or '7810201' in ma_nganh or '7510605' in ma_nganh):
        return 'Khoa Kinh tế quản trị'
    elif ('7340301' in ma_nganh or '7340201' in ma_nganh):
        return 'Khoa Kế toán - Tài chính'
    elif ('7220201' in ma_nganh or '7310608' in ma_nganh or '7220204' in ma_nganh):
        return 'Khoa Ngoại ngữ'
    else:
        return None

def remove_accent(text):
    if isinstance(text, str):
        return unidecode(text)
    return text

def unicode_hoten(df):
    hoten = (df['Họ'].apply(remove_accent) + ' ' + df['Tên'].apply(remove_accent) +
             ' ' + df['Điện Thoại'] +
             ' ' + df['Ngày Sinh'].str.replace(r'/', '', regex=True) +
             ' ' + 'XETHB2025')
    return hoten

def remove_extra_spaces(text):
    if isinstance(text, str):
        return ' '.join(text.split())
    return text

def wrangling(path):
    # Đọc file Excel
    df = pd.read_excel(path, dtype=str)

     # Chuyển đổi cột 'Ngày đăng ký' sang kiểu datetime
    df['Ngày đăng ký'] = pd.to_datetime(df['Ngày đăng ký'], format='%d/%m/%Y', errors='coerce')

    # Kiểm tra giá trị không hợp lệ trong cột 'Ngày đăng ký'
    if df['Ngày đăng ký'].isnull().any():
        raise ValueError("Cột 'Ngày đăng ký' chứa giá trị không hợp lệ hoặc bị thiếu.")

    # Định dạng lại Họ và Tên
    df['Họ'] = df['Họ'].str.title()
    df['Tên'] = df['Tên'].str.title()

# Điểm khu vực
    df['diem_khuvuc'] = df['Khu Vực theo THPT'].apply({'KV 1': 0.75, 'KV 2-NT': 0.5, 'KV 2': 0.25}.get).fillna(0)

    # Ánh xạ Khoa từ mã ngành
    df['Khoa_100'] = df['Mã ngành_100'].apply(assign_khoa)
    df['Khoa_200'] = df['Mã ngành_200'].apply(assign_khoa)
    df['Khoa_402'] = df['Mã ngành_402'].apply(assign_khoa)
    df['Khoa_thang'] = df['Mã ngành_tuyển thẳng'].apply(assign_khoa)

    # Xử lý số điện thoại
    df['dien_thoai_HS'] = '84' + df['Điện Thoại'].str[1:]
    df['dien_thoai_PH'] = '84' + df['Số điện thoại phụ huynh'].str[1:]

    # Cú pháp lệ phí 40.000
    df['cu_phap_40k'] = unicode_hoten(df)

    # Kiểm tra thông tin thiếu
    lst1 = ['Họ', 'Tên', 'Giới Tính', 'Ngày Sinh', 'Điện Thoại',
            'Số CMCD/CCCD', 'Email', 'Nơi sinh', 'Dân tộc', 'Mã Tỉnh', 'Mã Huyện',
            'Địa chỉ liên lạc']
    lst2 = ['Năm tốt nghiệp', 'Khu Vực theo THPT', 'Tỉnh THPT', 'Mã tỉnh THPT',
            'Mã trường THPT', 'Trường THPT']
    lst3 = ['Mã ngành_200', 'Hình thức', 'Tổ hợp', 'Môn 1', 'Môn 2', 'Môn 3',
            'Tổng điểm']
    lst4 = ['Học lực 12', 'Hạnh kiểm 12']
    lst5 = ['Có học bạ', 'Bằng tốt nghiệp', 'Chứng nhận KQ thi TN',
            'Hình CMND/CCCD']
    lst = lst1 + lst2 + lst3 + lst4 + lst5
    thieu_thongtin = pd.DataFrame(index=df.index)
    for item in lst1:
        for index, row in df.iterrows():
            if pd.isnull(row[item]):
                thieu_thongtin.loc[index, 'Thong_tin_thieu'] = f'[Thông tin thí sinh]'

    thieu_thongtin['THPT'] = ''
    for item in lst2:
        for index, row in df.iterrows():
            if pd.isnull(row[item]):
                thieu_thongtin.loc[index, 'THPT'] = f'[Quá trình học THPT]'

    thieu_thongtin['NV'] = ''
    for item in lst3:
        for index, row in df.iterrows():
            if pd.isnull(row[item]):
                thieu_thongtin.loc[index, 'NV'] = f'[Thông tin đăng ký nguyện vọng]'

    thieu_thongtin['HLHK'] = ''
    for item in lst4:
        for index, row in df.iterrows():
            if pd.isnull(row[item]):
                thieu_thongtin.loc[index, 'HLHK'] = f'[Học lực, hạnh kiểm]'

    thieu_thongtin['scan'] = ''
    for item in lst5:
        for index, row in df.iterrows():
            if row[item] == '0':
                thieu_thongtin.loc[index, 'scan'] = f'[File scan hồ sơ thí sinh]'

    thieu_thongtin['cu_the'] = ''
    for item in lst:
        for index, row in df.iterrows():
            if pd.isnull(row[item]):
                thieu_thongtin.loc[index, 'cu_the'] += f'[{item}] '
            elif row[item] == '0':
                thieu_thongtin.loc[index, 'cu_the'] += f'[{item}] '

    thieu_thongtin.fillna("", inplace=True)

    df['ZNS1_thieu'] = (thieu_thongtin['Thong_tin_thieu'] + ' '
                        + thieu_thongtin['THPT'] + ' '
                        + thieu_thongtin['NV'] + ' '
                        + thieu_thongtin['HLHK'] + ' '
                        + thieu_thongtin['scan'] + ' ')
    df['ZNS1_thieu'] = df['ZNS1_thieu'].apply(remove_extra_spaces)

    df['thieu_cu_the'] = thieu_thongtin['cu_the']
    df['ZNS2_thieu'] = thieu_thongtin['scan']

    # Ánh xạ tên ngành tuyển thẳng
    df['Tên ngành_tuyển thẳng'] = df['Mã ngành_tuyển thẳng'].map({
        '7720301': 'Điều dưỡng',
        '7220201': 'Ngôn ngữ Anh',
        '7340201': 'Tài chính - Ngân hàng',
        '7510605': 'Logistics và quản lý chuỗi cung ứng',
        '7220204': 'Ngôn ngữ Trung Quốc',
        '7480201': 'Công nghệ thông tin',
        '7480107': 'Trí tuệ nhân tạo',
        '7510301': 'Công nghệ kỹ thuật điện, điện tử',
        '7510202': 'Công nghệ chế tạo máy',
        '7480103': 'Kỹ thuật phần mềm',
        '7810201': 'Quản trị khách sạn',
        '7320104': 'Truyền thông đa phương tiện',
        '7340101': 'Quản trị kinh doanh',
        '7720601': 'Kỹ thuật xét nghiệm y học',
        '7210403': 'Thiết kế đồ họa',
        '7420201': 'Công nghệ sinh học',
        '7540101': 'Công nghệ thực phẩm',
        '7340301': 'Kế toán',
        '7510205': 'Công nghệ kỹ thuật ô tô',
        '7210408': 'Nghệ thuật số',
        '7510406': 'Công nghệ kỹ thuật môi trường',
        '7510401': 'Công nghệ kỹ thuật hóa học',
        '7810103': 'Quản trị dịch vụ du lịch và lữ hành',
        '7310608': 'Đông phương học',
        '7510103': 'Công nghệ kỹ thuật xây dựng'
    })

    return df

def thongke(df):
    # Đảm bảo cột 'Ngày đăng ký' là kiểu datetime
    if not pd.api.types.is_datetime64_any_dtype(df['Ngày đăng ký']):
        raise ValueError("Cột 'Ngày đăng ký' không phải kiểu datetime.")

    # Thống kê theo ngày
    dangky_days = df.groupby('Ngày đăng ký').size().reset_index(name='Số lượng đăng ký')

    # Thống kê theo tuần
    df['Tuần'] = df['Ngày đăng ký'].dt.isocalendar().week
    dangky_tuan = df.groupby('Tuần').size().reset_index(name='Số lượng đăng ký')

    # Thống kê theo tháng
    df['Tháng'] = df['Ngày đăng ký'].dt.month
    dangky_thang = df.groupby('Tháng').size().reset_index(name='Số lượng đăng ký')

    return dangky_days, dangky_tuan, dangky_thang

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                # Lưu file tải lên
                now = datetime.now()
                time = now.strftime("%d%m%y")
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(file_path)

                # Xử lý file
                df = wrangling(file_path)

                # Xuất file Excel (export-{time}.xlsx)
                excel_path = os.path.join(OUTPUT_FOLDER, f'export-{time}.xlsx')
                df.to_excel(excel_path, index=False)

                # Tạo file studio-looker-{time}.csv
                looker = df[['Số CMCD/CCCD', 'Giới Tính', 'Dân tộc', 'Khu Vực theo THPT',
                             'Tỉnh THPT', 'Trường THPT', 'Năm tốt nghiệp', 'Ngày đăng ký',
                             'Tên ngành_100', 'Tên ngành_200', 'Tên ngành_402',
                             'Mã ngành_tuyển thẳng', 'Khoa_100', 'Khoa_200', 'Khoa_402',
                             'Khoa_thang', 'dien_thoai_PH', 'Hoàn thành', 'Đã kiểm tra',
                             'Có học bạ', 'Bằng tốt nghiệp', 'Chứng nhận KQ thi TN', 'ZNS1_thieu']]
                csv_path = os.path.join(OUTPUT_FOLDER, f'studio-looker-{time}.csv')
                looker.to_csv(csv_path, index=False, encoding='utf-8-sig')

                # Tạo file TK-DWM-{time}.xlsx
                dangky_days, dangky_tuan, dangky_thang = thongke(df)
                tk_excel_path = os.path.join(OUTPUT_FOLDER, f'TK-DWM-{time}.xlsx')
                with pd.ExcelWriter(tk_excel_path, engine='xlsxwriter') as writer:
                    dangky_days.to_excel(writer, sheet_name='Tk Theo ngày', index=False)
                    dangky_tuan.to_excel(writer, sheet_name='Tk Theo tuần', index=False)
                    dangky_thang.to_excel(writer, sheet_name='Tk Theo tháng', index=False)

                # Nén các file cần thiết vào file ZIP với cấu trúc content/output/
                zip_path = os.path.join(OUTPUT_FOLDER, f'{time}.zip')
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    # Thêm file export-{time}.xlsx vào content/output/
                    zipf.write(excel_path, os.path.join('content/output', os.path.basename(excel_path)))

                    # Thêm file studio-looker-{time}.csv vào content/output/
                    zipf.write(csv_path, os.path.join('content/output', os.path.basename(csv_path)))

                    # Thêm file TK-DWM-{time}.xlsx vào content/output/
                    zipf.write(tk_excel_path, os.path.join('content/output', os.path.basename(tk_excel_path)))

                # Trả về giao diện với link tải file ZIP
                return render_template('index.html', success=True, download_link=zip_path)

            except Exception as e:
                return render_template('index.html', success=False, error=str(e))
    return render_template('index.html', success=None)

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)