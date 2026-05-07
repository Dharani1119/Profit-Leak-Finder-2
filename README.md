# 💸 Profit Leak Finder 2.0

> A simple, premium AI-powered business profit assistant for small business owners.

---

## 🚀 Deploy in 3 Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Profit Leak Finder 2.0"
git remote add origin https://github.com/YOUR_USERNAME/profit-leak-finder.git
git push -u origin main
```

### 2. Go to Streamlit Cloud
Visit **https://share.streamlit.io** → Sign in with GitHub

### 3. Deploy
- Repository: `your-username/profit-leak-finder`
- Branch: `main`
- Main file: `app.py`
- Click **Deploy!**

---

## 📁 Project Structure
```
profit-leak-finder/
├── app.py                  ← Main Streamlit app
├── requirements.txt        ← Python packages
├── .streamlit/
│   └── config.toml         ← Dark purple theme
├── sample_data/
│   ├── sample_sales.csv    ← Demo sales data
│   ├── sample_expenses.csv ← Demo expense data
│   └── sample_products.csv ← Demo product list
└── README.md
```

---

## 📊 Features

- **Demo Mode** — Try instantly with one click, no upload needed
- **Business Health Score** — Simple 0–100 score with breakdown
- **Sales Overview** — Revenue & profit trends over time
- **Best-Selling Products** — See what's working
- **Where Your Money Goes** — Expense breakdown
- **Hidden Profit Leaks** — Alerts for losing products, spending spikes
- **Smart Suggestions** — Simple, actionable tips
- **Download Report** — Take your insights with you

---

## 📂 CSV Column Requirements

### Sales CSV
| Date | Product | Quantity | Unit_Price | Unit_COGS |

### Expenses CSV
| Date | Category | Amount |

### Products CSV
| Product | Category | Unit_Price | Unit_COGS | Stock |

---

## 🛠️ Tech Stack
Streamlit · Pandas · Plotly · NumPy · OpenPyXL
