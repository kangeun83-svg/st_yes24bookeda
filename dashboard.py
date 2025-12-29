import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
import os

# --- Configuration & Setup ---
st.set_page_config(
    page_title="Yes24 IT Book Dashboard",
    page_icon="📚",
    layout="wide"
)

# --- Data Loading ---
@st.cache_data
def load_data():
    file_path = 'book_data.csv'
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    
    # Preprocessing
    def clean_price(price):
        if isinstance(price, str):
            return int(price.replace(',', '').replace('원', ''))
        return price

    df['Price'] = df['Price'].apply(clean_price)
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    df['Review Count'] = pd.to_numeric(df['Review Count'], errors='coerce')
    df['Sales Index'] = pd.to_numeric(df['Sales Index'], errors='coerce').fillna(0)
    
    # Date parsing
    def parse_date(date_str):
        try:
            return pd.to_datetime(date_str, format='%Y년 %m월')
        except:
            return pd.to_datetime(date_str, errors='coerce')
            
    df['Publishing Date'] = df['Publishing Date'].apply(parse_date)
    df['YearMonth'] = df['Publishing Date'].dt.to_period('M').astype(str)
    
    return df

df = load_data()

# --- Helper Function for Section ---
def section_header(title, explanation):
    st.markdown(f"### {title}")
    st.info(explanation)

def show_data_table(data, title="Data Table"):
    with st.expander(f"View {title}"):
        st.dataframe(data)

# --- Sidebar Navigation ---
st.sidebar.title("📚 Navigation")
menu = st.sidebar.radio(
    "Go to",
    ["홈 (Home)", "판매 및 랭킹 (Sales)", "출판사 분석 (Publisher)", "가격 및 평점 (Price & Rating)", "키워드 검색 (Search)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 Yes24 Analysis Team")

if df is None:
    st.error("데이터 파일을 찾을 수 없습니다. 'book_data.csv' 파일이 같은 경로에 있는지 확인해주세요.")
    st.stop()

# --- Page 1: Home ---
if "홈" in menu:
    st.title("📊 Yes24 IT 도서 분석 대시보드")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 도서 수", f"{len(df)}권")
    col2.metric("평균 가격", f"{df['Price'].mean():,.0f}원")
    col3.metric("평균 평점", f"{df['Rating'].mean():.1f}점")
    col4.metric("총 리뷰 수", f"{df['Review Count'].sum():,}개")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📝 개요", "📈 최근 트렌드", "📋 데이터 미리보기"])
    
    with tab1:
        st.markdown("""
        ### 대시보드 개요
        이 대시보드는 수집된 Yes24 IT 분야 도서 데이터를 기반으로 다양한 인사이트를 제공합니다.
        
        - **판매 분석**: 판매지수가 높은 베스트셀러를 파악합니다.
        - **출판사 분석**: 주요 출판사의 출간 경향과 평점을 분석합니다.
        - **가격 가이드**: 도서 정가 책정의 기준이 될 수 있는 가격 분포를 확인합니다.
        
        데이터 분석을 통해 시장의 흐름을 읽고 전략적인 의사결정을 내리는 데 도움을 줄 수 있습니다.
        """)
    
    with tab2:
        section_header("월별 도서 출판 추이", 
                       "이 그래프는 시간에 따른 IT 도서의 출판 수 변화를 보여줍니다. 특정 시기에 출판량이 급증하거나 감소하는 패턴을 파악하여, 계절성 요인이나 시장의 트렌드 변화를 유추해볼 수 있습니다. 예를 들어, 신학기 시즌이나 연말에 출판량이 늘어나는 경향이 있는지 확인해 보세요.")
        
        monthly_counts = df.groupby('YearMonth').size().reset_index(name='Count')
        fig = px.line(monthly_counts, x='YearMonth', y='Count', markers=True, title="Monthly Publishing Trend")
        st.plotly_chart(fig, use_container_width=True)
        show_data_table(monthly_counts)
        
    with tab3:
        st.dataframe(df.head(20))

# --- Page 2: Sales & Ranking ---
elif "판매" in menu:
    st.title("🏆 판매 및 랭킹 분석")
    
    tab1, tab2, tab3 = st.tabs(["🔥 판매지수 TOP 20", "📊 판매지수 vs 리뷰", "📅 출판사별 판매지수"])
    
    with tab1:
        section_header("판매지수 상위 20개 도서", 
                       "판매지수는 해당 도서의 인기를 가장 직관적으로 보여주는 지표입니다. 상위 20개 도서를 분석함으로써 현재 시장을 주도하는 트렌드 키워드(예: AI, Python, 챗GPT 등)가 무엇인지 파악할 수 있습니다. 상위권 도서들의 공통점을 찾아 벤치마킹하는 전략이 필요합니다.")
        
        top_sales = df.nlargest(20, 'Sales Index')
        fig = px.bar(top_sales, x='Sales Index', y='Title', orientation='h', 
                     color='Sales Index', hover_data=['Publisher', 'Author'],
                     title="Top 20 Books by Sales Index")
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        show_data_table(top_sales[['Title', 'Sales Index', 'Publisher', 'Author']])
        
    with tab2:
        section_header("판매지수와 리뷰 수의 상관관계", 
                       "일반적으로 리뷰가 많으면 판매지수도 높을 것으로 예상되지만, 항상 그런 것은 아닙니다. 이 산점도를 통해 리뷰 수는 적지만 판매지수가 높은 '숨은 강자' 도서나, 리뷰는 많지만 판매지수는 상대적으로 낮은 도서들을 식별할 수 있습니다. 마케팅 효율성을 점검하는 데 유용한 지표입니다.")
        
        fig = px.scatter(df, x='Review Count', y='Sales Index', 
                         color='Rating', size='Price', hover_data=['Title'],
                         title="Sales Index vs Review Count")
        st.plotly_chart(fig, use_container_width=True)
        
        # Cross-tab
        crosstab = pd.crosstab(pd.cut(df['Review Count'], bins=5), pd.cut(df['Sales Index'], bins=5))
        show_data_table(crosstab, "Review Count vs Sales Index Grouping")
        
    with tab3:
        section_header("주요 출판사별 평균 판매지수", 
                       "어떤 출판사가 평균적으로 높은 판매지수를 기록하고 있는지 비교합니다. 이는 출판사의 브랜드 파워나 마케팅 역량을 간접적으로 보여줄 수 있습니다. 상위 출판사들은 어떤 종류의 책을 주로 내는지 추가적으로 분석해볼 가치가 있습니다.")
        
        top_pubs = df['Publisher'].value_counts().nlargest(10).index
        filtered_df = df[df['Publisher'].isin(top_pubs)]
        avg_sales = filtered_df.groupby('Publisher')['Sales Index'].mean().sort_values(ascending=False).reset_index()
        
        fig = px.bar(avg_sales, x='Publisher', y='Sales Index', color='Publisher',
                     title="Average Sales Index by Top 10 Publishers")
        st.plotly_chart(fig, use_container_width=True)
        show_data_table(avg_sales)

# --- Page 3: Publisher Insights ---
elif "출판사" in menu:
    st.title("🏢 출판사 심층 분석")
    
    # Publisher Selection
    publisher_list = df['Publisher'].unique().tolist()
    selected_publisher = st.selectbox("분석할 출판사를 선택하세요:", sorted(publisher_list))
    
    pub_df = df[df['Publisher'] == selected_publisher]
    
    # Publisher Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("출간 도서 수", f"{len(pub_df)}권")
    col2.metric("평균 판매지수", f"{pub_df['Sales Index'].mean():,.0f}")
    col3.metric("평균 평점", f"{pub_df['Rating'].mean():.1f}점")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["💰 가격 분포", "⭐ 평점 분포", "📈 연도별 출간 활동"])
    
    with tab1:
        section_header(f"{selected_publisher} - 가격 분포", 
                       f"선택한 출판사({selected_publisher})의 도서 가격 정책을 엿볼 수 있습니다. 특정 가격대에 집중되어 있는지, 아니면 저가부터 고가까지 다양한 라인업을 갖추고 있는지 확인해 보세요. 경쟁사의 가격 전략을 분석하는 데 도움이 됩니다.")
        
        fig = px.histogram(pub_df, x='Price', nbins=20, title=f"Price Distribution for {selected_publisher}",
                           marginal="box")
        st.plotly_chart(fig, use_container_width=True)
        show_data_table(pub_df['Price'].describe().to_frame())
        
    with tab2:
        section_header(f"{selected_publisher} - 평점 분포", 
                       f"{selected_publisher}의 도서들이 독자들에게 어떤 평가를 받고 있는지 보여줍니다. 평점이 전반적으로 높다면 콘텐츠의 품질 관리가 잘 되고 있다는 신호입니다. 반면 낮은 평점의 도서가 많다면 원인 분석이 필요합니다.")
        
        fig = px.histogram(pub_df, x='Rating', nbins=10, range_x=[0, 10], color_discrete_sequence=['orange'],
                           title=f"Rating Distribution for {selected_publisher}")
        st.plotly_chart(fig, use_container_width=True)
        show_data_table(pub_df['Rating'].value_counts(bins=5).sort_index().to_frame())
        
    with tab3:
        section_header(f"{selected_publisher} - 시간 흐름에 따른 출간", 
                       f"이 출판사의 출간 활동이 활발한지, 혹은 뜸해지고 있는지 트렌드를 확인할 수 있습니다. 지속적으로 신간을 내고 있는 출판사인지 파악하는 것은 파트너십이나 경쟁 분석에 중요합니다.")
        
        pub_trend = pub_df.groupby('YearMonth').size().reset_index(name='Count')
        if not pub_trend.empty:
            fig = px.bar(pub_trend, x='YearMonth', y='Count', title=f"Publishing Activity Over Time ({selected_publisher})")
            st.plotly_chart(fig, use_container_width=True)
            show_data_table(pub_trend)
        else:
            st.warning("데이터가 충분하지 않아 트렌드를 표시할 수 없습니다.")

# --- Page 4: Price & Rating ---
elif "가격" in menu:
    st.title("💸 가격 및 평점 상관관계")
    
    tab1, tab2, tab3 = st.tabs(["📦 가격대별 분포 (Boxplot)", "📉 상관관계 히트맵", "📊 가격대별 판매지수"])
    
    with tab1:
        section_header("상위 출판사 가격 분포 비교", 
                       "책을 많이 낸 상위 10개 출판사의 가격 정책을 한눈에 비교할 수 있는 박스 플롯입니다. 상자(Box)의 위치가 높을수록 고가 정책을, 낮을수록 저가 정책을 의미합니다. 상자의 길이는 가격의 다양성(변동성)을 나타냅니다.")
        
        top_pubs = df['Publisher'].value_counts().nlargest(10).index
        fig = px.box(df[df['Publisher'].isin(top_pubs)], x='Publisher', y='Price', color='Publisher',
                     title="Price Distribution by Top 10 Publishers")
        st.plotly_chart(fig, use_container_width=True)
        
        # Pivot table
        pivot = df[df['Publisher'].isin(top_pubs)].groupby('Publisher')['Price'].describe()
        show_data_table(pivot)
        
    with tab2:
        section_header("주요 지표 간 상관관계 분석", 
                       "가격, 평점, 리뷰 수, 판매지수 간에 어떤 관련성이 있는지 색상으로 표현한 히트맵입니다. 1에 가까울수록(붉은색) 강한 양의 상관관계, -1에 가까울수록(푸른색) 강한 음의 상관관계가 있습니다. 예를 들어 가격과 판매지수가 양의 상관관계라면, 비싼 책이 더 잘 팔린다는 뜻일 수 있습니다.")
        
        corr = df[['Price', 'Rating', 'Review Count', 'Sales Index']].corr()
        fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto",
                        title="Correlation Heatmap")
        st.plotly_chart(fig, use_container_width=True)
        show_data_table(corr)
        
    with tab3:
        section_header("가격 구간별 평균 판매지수", 
                       "가격을 1만원 단위 구간으로 나누어, 어느 가격대의 책이 가장 판매지수가 높은지 분석합니다. 이를 통해 독자들이 선호하는 '적정 가격대'를 추정해볼 수 있으며, 신규 도서 가격 책정 시 참고할 수 있는 중요한 데이터입니다.")
        
        df['Price Range'] = pd.cut(df['Price'], bins=[0, 15000, 25000, 35000, 50000, 100000], 
                                   labels=['~1.5만', '1.5~2.5만', '2.5~3.5만', '3.5~5.0만', '5.0만+'])
        price_sales = df.groupby('Price Range')['Sales Index'].mean().reset_index()
        
        fig = px.bar(price_sales, x='Price Range', y='Sales Index', 
                     title="Average Sales Index by Price Range")
        st.plotly_chart(fig, use_container_width=True)
        show_data_table(price_sales)

# --- Page 5: Keyword Search ---
elif "키워드" in menu:
    st.title("🔍 키워드 검색 및 분석")
    
    st.markdown("""
    관심 있는 키워드를 입력하여 도서를 검색하고, 해당 도서들의 트렌드를 분석해보세요.
    빈 칸으로 두면 전체 도서를 대상으로 분석합니다.
    """)
    
    keyword = st.text_input("검색할 키워드를 입력하세요 (예: AI, 파이썬, 입문):")
    
    if keyword:
        filtered_df = df[df['Title'].str.contains(keyword, case=False) | df['Subtitle'].fillna('').str.contains(keyword, case=False)]
    else:
        filtered_df = df
        
    st.info(f"검색 결과: 총 {len(filtered_df)}권의 도서가 발견되었습니다.")
    
    tab1, tab2, tab3 = st.tabs(["☁️ 워드클라우드", "📋 도서 목록", "📊 검색 도서 통계"])
    
    with tab1:
        section_header("도서 제목 워드클라우드", 
                       "검색된 도서들의 제목에서 가장 많이 등장하는 단어를 시각화했습니다. 글자가 클수록 더 자주 등장하는 키워드입니다. 이를 통해 해당 주제와 연관된 '연관검색어'나 '핫한 토픽'을 직관적으로 파악할 수 있습니다.")
        
        if not filtered_df.empty:
            text = ' '.join(filtered_df['Title'].fillna('') + ' ' + filtered_df['Subtitle'].fillna(''))
            # Simple regex for words
            words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
            stopwords = ['부제', '없음', 'Guide', '가이드', '완벽', '실전', '입문', '기초', '활용', '저자', '옮김', '지음', '코딩']
            words = [w for w in words if w not in stopwords and len(w) > 1]
            
            if words:
                wc = WordCloud(font_path='C:/Windows/Fonts/malgun.ttf', width=800, height=400, background_color='white').generate(' '.join(words))
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            else:
                st.warning("워드클라우드를 생성할 충분한 텍스트가 없습니다.")
        else:
            st.warning("검색 결과가 없습니다.")
            
    with tab2:
        section_header("검색 도서 상세 목록", "검색 조건에 맞는 도서들의 상세 정보를 테이블 형태로 제공합니다. 제목, 저자, 출판사, 가격, 판매지수 등을 한눈에 비교하고 확인할 수 있습니다.")
        st.dataframe(filtered_df[['Title', 'Publisher', 'Price', 'Rating', 'Sales Index', 'Publishing Date']])
        
    with tab3:
        section_header("검색 결과 요약 통계", "검색된 도서 집단의 평균적인 특성을 보여줍니다. 전체 도서 평균과 비교해보면, 해당 키워드를 가진 책들이 더 비싼지, 더 인기가 많은지 등의 인사이트를 얻을 수 있습니다.")
        if not filtered_df.empty:
            stats = filtered_df[['Price', 'Rating', 'Sales Index']].describe()
            st.dataframe(stats)
            
            # Simple bar chart for Sales Index of top 5 in search
            top_search = filtered_df.nlargest(5, 'Sales Index')
            fig = px.bar(top_search, x='Sales Index', y='Title', orientation='h', title="Top 5 Sales in Search Result")
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
