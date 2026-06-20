import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# Cấu hình trang web Streamlit
st.set_page_config(page_title="So Sánh Đầu Tư", layout="wide")
st.title("📊 Công Cụ So Sánh Tích Lũy: Tiết Kiệm vs Cổ Phiếu_HS PHÙNG CÔNG BÁCH")
st.caption("Dữ liệu cổ phiếu được lấy chuẩn xác theo giá điều chỉnh từ Yahoo Finance.")

# --- THANH ĐIỀU KHIỂN (SIDEBAR) ---
st.sidebar.header("⚙️ Cấu Hình Thông Số")

# Chọn chế độ tích lũy
co_che = st.sidebar.radio(
    "Chọn cơ chế tích lũy:",
    ("Mua một cục ban đầu (Lump-sum)", "Tích lũy hàng tháng (DCA)")
)

# Nhập các thông số tài chính
ticker = st.sidebar.text_input("Mã cổ phiếu (Ví dụ: FPT.VN, VNM.VN, E1VFVN30.VN):", "FPT.VN")
vons_bandau = st.sidebar.number_input("Số vốn ban đầu (VND):", min_value=0, value=10000000, step=1000000)

# Hiện ô nhập tiền hàng tháng nếu chọn DCA
if co_che == "Tích lũy hàng tháng (DCA)":
    dca_hangthang = st.sidebar.number_input("Số tiền nạp thêm mỗi tháng (VND):", min_value=0, value=2000000, step=500000)
else:
    dca_hangthang = 0

lai_suat_nam = st.sidebar.number_input("Lãi suất tiết kiệm (%/năm):", min_value=0.0, value=6.0, step=0.5) / 100
K_nam = st.sidebar.slider("Thời gian backtest (Năm):", min_value=1, max_value=10, value=5)

# --- XỬ LÝ DỮ LIỆU ---
if st.sidebar.button("📊 Tính Toán Kết Quả", type="primary"):
    with st.spinner("Đang tải dữ liệu cổ phiếu..."):
        # Tải dữ liệu lịch sử theo tháng
        period_str = f"{K_nam}y"
        data = yf.download(ticker, period=period_str, interval="1mo")
        
        if not data.empty:
            # LÀM SẠCH DỮ LIỆU: Xử lý lỗi tiêu đề nhiều tầng (MultiIndex) của yfinance bản mới
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            
            # 1. Sắp xếp lại index theo thứ tự thời gian tăng dần để tránh lỗi đan chéo đường vẽ
            data = data.sort_index()
            
            # 2. LỌC BỎ NHIỄU RĂNG CƯA: Loại bỏ các dòng chốt quyền ảo bằng cách giữ lại dòng có Volume > 0
            if 'Volume' in data.columns:
                data['Volume'] = data['Volume'].fillna(0)
                data = data[data['Volume'] > 0]
            
            # 3. Loại bỏ trùng lặp ngày nếu có phát sinh
            data = data[~data.index.duplicated(keep='first')]
            
            # Chọn cột giá thích hợp
            target_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
            prices = data[target_col].dropna()
            
            if not prices.empty:
                df_calc = pd.DataFrame(index=prices.index)
                df_calc['Stock_Price'] = prices
                
                # 1. Tính toán kênh Tiết Kiệm
                tk_assets = []
                current_tk = vons_bandau
                for i in range(len(df_calc)):
                    if i > 0:
                        current_tk = current_tk * (1 + lai_suat_nam / 12) + dca_hangthang
                    tk_assets.append(current_tk)
                df_calc['Tiet_Kiem'] = tk_assets
                
                # 2. Tính toán kênh Cổ Phiếu
                stock_assets = []
                total_shares = 0
                tong_goc_da_nap = 0
                
                for i, price in enumerate(df_calc['Stock_Price']):
                    if i == 0:
                        total_shares += vons_bandau / price
                        tong_goc_da_nap += vons_bandau
                    else:
                        total_shares += dca_hangthang / price
                        tong_goc_da_nap += dca_hangthang
                    
                    stock_assets.append(total_shares * price)
                    
                df_calc['Co_Phieu'] = stock_assets
                
                # Kết quả cuối cùng
                final_tk = df_calc['Tiet_Kiem'].iloc[-1]
                final_stock = df_calc['Co_Phieu'].iloc[-1]
                
                # --- HIỂN THỊ KẾT QUẢ KINH DOANH ---
                col1, col2, col3 = st.columns(3)
                col1.metric("Tổng Vốn Gốc Đã Nạp", f"{tong_goc_da_nap:,.0f} VND")
                col2.metric("Giá trị Tiết Kiệm thu về", f"{final_tk:,.0f} VND", f"Lãi: {(final_tk - tong_goc_da_nap):,.0f} VND")
                col3.metric(f"Giá trị Cổ Phiếu ({ticker})", f"{final_stock:,.0f} VND", f"Chênh lệch: {(final_stock - final_tk):,.0f} VND", delta_color="normal")
                
                # --- VẼ BIỂU ĐỒ TÍCH LŨY ---
                st.subheader("📈 Biểu Đồ Tăng Trưởng Tài Sản Qua Các Năm")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_calc.index, y=df_calc['Tiet_Kiem'], name='Tài sản Tiết Kiệm', line=dict(color='#A3A3A3', width=2)))
                fig.add_trace(go.Scatter(x=df_calc.index, y=df_calc['Co_Phieu'], name=f'Tài sản Cổ Phiếu ({ticker})', line=dict(color='#8B5CF6', width=3)))
                
                fig.update_layout(
                    hovermode="x unified",
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Số tiền (VND)")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Dữ liệu giá cổ phiếu trống sau khi làm sạch nhiễu.")
        else:
            st.error(f"Không thể lấy dữ liệu cho mã '{ticker}'. Hãy kiểm tra lại ký tự mã (Ví dụ mã sàn VN cần thêm đuôi .VN như FPT.VN).")
