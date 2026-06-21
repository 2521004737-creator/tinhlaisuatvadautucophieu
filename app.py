import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# Cấu hình trang web Streamlit
st.set_page_config(page_title="So Sánh Đầu Tư", layout="wide")
st.title("📊 Công Cụ So Sánh Tích Lũy: Tiết Kiệm vs Cổ Phiếu / ETF")
st.caption("Dữ liệu được tối ưu hóa tự động cho cả Cổ phiếu và Quỹ ETF từ Yahoo Finance.")

# --- THANH ĐIỀU KHIỂN (SIDEBAR) ---
st.sidebar.header("⚙️ Cấu Hình Thông Số")

co_che = st.sidebar.radio(
    "Chọn cơ chế tích lũy:",
    ("Mua một cục ban đầu (Lump-sum)", "Tích lũy hàng tháng (DCA)")
)

ticker = st.sidebar.text_input("Mã chứng khoán (Ví dụ: FPT.VN, VIC.VN, E1VFVN30.VN, FUEVFVND.VN):", "E1VFVN30.VN")
vons_bandau = st.sidebar.number_input("Số vốn ban đầu (VND):", min_value=0, value=10000000, step=1000000)

if co_che == "Tích lũy hàng tháng (DCA)":
    dca_hangthang = st.sidebar.number_input("Số tiền nạp thêm mỗi tháng (VND):", min_value=0, value=2000000, step=500000)
else:
    dca_hangthang = 0

lai_suat_nam = st.sidebar.number_input("Lãi suất tiết kiệm (%/năm):", min_value=0.0, value=6.0, step=0.5) / 100
K_nam = st.sidebar.slider("Thời gian muốn backtest tối đa (Năm):", min_value=1, max_value=10, value=5)

# --- XỬ LÝ DỮ LIỆU ---
if st.sidebar.button("📊 Tính Toán Kết Quả", type="primary"):
    with st.spinner("Đang tải và xử lý dữ liệu chuẩn..."):
        period_str = f"{K_nam}y"
        ticker_obj = yf.Ticker(ticker)
        data = ticker_obj.history(period=period_str, interval="1d")
        
        if not data.empty:
            data = data.sort_index()
            raw_prices = data['Close'].dropna()
            
            try:
                prices = raw_prices.resample('ME').last().dropna()
            except ValueError:
                prices = raw_prices.resample('M').last().dropna()
            
            if not prices.empty:
                # TÍNH TOÁN SỐ NĂM THỰC TẾ ĐẦU TƯ KHẢ DỤNG
                so_thang_thuc_te = len(prices)
                so_nam_thuc_te = so_thang_thuc_te / 12
                
                # Hiển thị cảnh báo nếu mã không đủ lịch sử dữ liệu như slider yêu cầu
                if so_nam_thuc_te < (K_nam - 0.5):
                    st.warning(f"⚠️ Mã {ticker} mới hoạt động hoặc chỉ có dữ liệu thực tế trong **{so_nam_thuc_te:.1f} năm** ({so_thang_thuc_te} tháng). Hệ thống đã tự động điều chỉnh thời gian tính toán của cả 2 kênh về mốc này để đảm bảo so sánh công bằng.")
                else:
                    st.info(f"✅ Đang tiến hành so sánh hiệu suất trong vòng **{so_nam_thuc_te:.1f} năm** gần nhất.")

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
                
                # 2. Tính toán kênh Cổ Phiếu / ETF
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
                
                final_tk = df_calc['Tiet_Kiem'].iloc[-1]
                final_stock = df_calc['Co_Phieu'].iloc[-1]
                
                pct_tang_tk = ((final_tk - tong_goc_da_nap) / tong_goc_da_nap) * 100
                pct_tang_stock = ((final_stock - tong_goc_da_nap) / tong_goc_da_nap) * 100
                
                gia_dau_ky = df_calc['Stock_Price'].iloc[0]
                gia_cuoi_ky = df_calc['Stock_Price'].iloc[-1]
                cagr_stock = ((gia_cuoi_ky / gia_dau_ky) ** (1 / so_nam_thuc_te) - 1) * 100
                
                # --- HIỂN THỊ KẾT QUẢ KINH DOANH ---
                st.subheader("📈 Hiệu Suất Tổng Kết Quá Trình Tích Lũy")
                col1, col2, col3 = st.columns(3)
                col1.metric("Tổng Vốn Gốc Đã Nạp", f"{tong_goc_da_nap:,.0f} VND")
                
                col2.metric(
                    "Tài Sản Tiết Kiệm", 
                    f"{final_tk:,.0f} VND", 
                    f"Tổng lãi: +{pct_tang_tk:.2f}%"
                )
                
                col3.metric(
                    f"Tài Sản {ticker}", 
                    f"{final_stock:,.0f} VND", 
                    f"Tổng lãi: +{pct_tang_stock:.2f}%" if pct_tang_stock >= 0 else f"Tổng lỗ: {pct_tang_stock:.2f}%"
                )
                
                # --- THÔNG SỐ CHUYÊN SÂU ---
                st.write("---")
                st.subheader("📊 Chỉ Số Tăng Trưởng Riêng Của Chứng Khoán")
                col_cagr1, col_cagr2 = st.columns(2)
                
                col_cagr1.metric(
                    f"Lợi nhuận TB hàng năm (CAGR) của {ticker}", 
                    f"{cagr_stock:.2f}% / năm",
                    help="Tốc độ tăng trưởng kép hàng năm của thị giá tài sản dựa trên số năm dữ liệu thực tế."
                )
                
                chenh_lech_tien = final_stock - final_tk
                if chenh_lech_tien >= 0:
                    col_cagr2.success(f"🔥 Kênh chứng khoán giúp bạn KIẾM THÊM: {chenh_lech_tien:,.0f} VND so với gửi tiết kiệm.")
                else:
                    col_cagr2.warning(f"⚠️ Kênh chứng khoán khiến bạn THIỆT HẠI: {abs(chenh_lech_tien):,.0f} VND so với gửi tiết kiệm.")
                
                # --- VẼ BIỂU ĐỒ TÍCH LŨY ---
                st.write("---")
                st.subheader("📉 Biểu Đồ Diễn Biến Tăng Trưởng Tài Sản Qua Các Năm")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_calc.index, y=df_calc['Tiet_Kiem'], name='Tài sản Tiết Kiệm', line=dict(color='#A3A3A3', width=2)))
                fig.add_trace(go.Scatter(x=df_calc.index, y=df_calc['Co_Phieu'], name=f'Tài sản Chứng Khoán ({ticker})', line=dict(color='#8B5CF6', width=3)))
                
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
                st.error("Không thể xử lý dữ liệu sau khi đồng bộ theo tháng.")
        else:
            st.error(f"Không thể tải dữ liệu lịch sử cho mã '{ticker}'. Hãy chắc chắn rằng mã được nhập chính xác (Ví dụ đuôi .VN).")
