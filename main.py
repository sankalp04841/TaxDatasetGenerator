from faker import Faker
import random
import os
from reportlab.pdfgen import canvas
from pdfrw import PdfReader, PdfWriter, PdfDict

fake = Faker()

states = ["CA", "TX", "NY", "IL", "FL"]
years = [2020, 2021, 2022, 2023, 2024, 2025]
levels = ["easy", "medium", "complex"]

STANDARD_DEDUCTION_BY_YEAR = {
    2020: {"Single": 12400, "Married Filing Jointly": 24800, "Head of Household": 18650},
    2021: {"Single": 12550, "Married Filing Jointly": 25100, "Head of Household": 18800},
    2022: {"Single": 12950, "Married Filing Jointly": 25900, "Head of Household": 19400},
    2023: {"Single": 13850, "Married Filing Jointly": 27700, "Head of Household": 20800},
    2024: {"Single": 14600, "Married Filing Jointly": 29200, "Head of Household": 21900},
    2025: {"Single": 15000, "Married Filing Jointly": 30000, "Head of Household": 22500}
}

def create_state_summary(path, state_data):
    lines = [
        "=== STATE TAX SUMMARY REPORT ===",
        "",
        f"State: {state_data['state']}",
        "",
        "----- INCOME DETAILS -----",
        f"Total Income: {state_data['income']}",
        "",
        "----- TAX CALCULATION -----",
        f"Initial State Tax: {state_data['state_tax']}",
        "",
        "----- CREDITS APPLIED -----"
    ]

    if state_data["credits"]:
        for k, v in state_data["credits"].items():
            lines.append(f"{k:<20}: {v}")
    else:
        lines.append("No credits applied")

    total_credits = sum(state_data["credits"].values()) if state_data["credits"] else 0

    lines.extend([
        "",
        "----- SUMMARY -----",
        f"{'Total Credits':<20}: {total_credits}",
        f"{'Final Tax Liability':<20}: {state_data['final_tax']}",
        "",
        "----- STATUS -----"
    ])

    if state_data["final_tax"] < 0:
        lines.append(f"Refund Due        : {abs(state_data['final_tax'])}")
    elif state_data["final_tax"] > 0:
        lines.append(f"Amount Owed       : {state_data['final_tax']}")
    else:
        lines.append("No balance due")

    lines.extend([
        "",
        "----- NOTES -----",
        "Synthetic dataset for testing purposes.",
        "All values derived programmatically.",
        "No real personal data is used."
    ])

    create_pdf(path, lines) 

def create_client_summary(path, person, tax_data, state_data, filing_status):

    lines = [
        "=== CLIENT TAX SUMMARY REPORT ===",
        "",
        "----- PERSONAL INFORMATION -----",
        f"Name                : {person['name']}",
        f"SSN                 : {person['ssn']}",
        f"Filing Status       : {filing_status}",
        f"Address             : {person['address']}, {person['city']}, {person['state']} {person['zip']}",
        "",
        "----- INCOME BREAKDOWN -----",
        f"W-2 Income          : {person['w2_income']}",
        f"Interest Income     : {person['interest_income']}",
        f"Dividend Income     : {person['dividend_income']}",
        f"Freelance Income    : {person['freelance_income']}",
        "",
        "----- FEDERAL TAX SUMMARY -----",
        f"Total Income        : {tax_data['total_income']}",
        f"Adjusted Gross Income (AGI): {tax_data['agi']}",
        f"Taxable Income      : {tax_data['taxable_income']}",
        f"Federal Tax (Before Credits): {tax_data['raw_tax']}",
        f"Final Tax (After Credits)   : {tax_data['final_tax']}",
        "",
        "----- CREDITS -----",
        f"Child Tax Credit    : {tax_data['ctc']}",
        f"EITC                : {tax_data['eitc']}",
        "",
        "----- PAYMENTS -----",
        f"Tax Withheld        : {person['tax_withheld']}",
        "",
        "----- RESULT -----"
    ]

    if tax_data["refund"] > 0:
        lines.append(f"Refund              : {tax_data['refund']}")
    else:
        lines.append(f"Amount Owed         : {abs(tax_data['refund'])}")

    lines.extend([
        "",
        "----- STATE SUMMARY -----",
        f"State               : {state_data['state']}",
        f"State Tax           : {state_data['state_tax']}",
        f"Final State Tax     : {state_data['final_tax']}",
        "",
        "----- NOTES -----",
        "This is a synthetic tax report generated for testing.",
        "All data is fictional and consistent across documents."
    ])

    create_pdf(path, lines)


def generate_state_data(state, person, tax_data):
    income = tax_data["total_income"]

    state_data = {
        "state": state,
        "income": income,
        "state_tax": 0,
        "credits": {},
        "final_tax": 0
    }

    # -------- CALIFORNIA --------
    if state == "CA":
        state_tax = int(income * 0.05)

        cal_eitc = int(income * 0.05) if income < 30000 else 0
        yctc = 1000 if any(c["age"] < 6 for c in person["children"]) else 0
        renters_credit = random.choice([0, 60, 120])

        total_credits = cal_eitc + yctc + renters_credit

        state_data.update({
            "state_tax": state_tax,
            "credits": {
                "CalEITC": cal_eitc,
                "YCTC": yctc,
                "RentersCredit": renters_credit
            },
            "final_tax": state_tax - total_credits
        })

    # -------- NEW YORK --------
    elif state == "NY":
        state_tax = int(income * 0.04)
        nyc_tax = int(income * 0.03)

        child_credit = len(person["children"]) * 500

        total_tax = state_tax + nyc_tax
        final_tax = total_tax - child_credit

        state_data.update({
            "state_tax": total_tax,
            "credits": {
                "NYChildCredit": child_credit
            },
            "final_tax": final_tax
        })

    # -------- ILLINOIS --------
    elif state == "IL":
        state_tax = int(income * 0.0495)

        state_data.update({
            "state_tax": state_tax,
            "credits": {},
            "final_tax": state_tax
        })

    # -------- TEXAS / FLORIDA --------
    elif state in ["TX", "FL"]:
        state_data.update({
            "state_tax": 0,
            "credits": {},
            "final_tax": 0
        })

    return state_data


def fill_schedule_se(template_path, output_path, person, schedule_c):

    pdf = PdfReader(template_path)

    name = person["name"]
    ssn = person["ssn"].replace("-", "")

    net_profit = schedule_c["net_profit"]

    # ---- Core calculations (simplified but realistic) ----
    line_5 = net_profit
    line_6 = line_5
    line_7 = round(line_6 * 0.9235)
    line_9 = line_7

    # Social Security + Medicare
    ss_tax = round(line_7 * 0.124)
    medicare_tax = round(line_7 * 0.029)

    total_se_tax = ss_tax + medicare_tax
    deduction = round(total_se_tax * 0.5)

    wages = person["w2_income"]

    data = {
        "f1_01[0]": name,
        "f1_02[0]": ssn,

        # Farm (not used)
        "f1_3[0]": "0",
        "f1_4[0]": "0",

        # Business income (IMPORTANT)
        "f1_5[0]": str(line_5),

        "f1_6[0]": str(line_6),
        "f1_7[0]": str(line_7),

        "f1_8[0]": "0",
        "f1_9[0]": str(line_9),

        "f1_10[0]": "0",
        "f1_11[0]": str(line_7),
        "f1_12[0]": str(line_7),

        # W2 linkage
        "f1_14[0]": str(wages),
        "f1_15[0]": "0",
        "f1_16[0]": "0",
        "f1_17[0]": str(wages),

        "f1_18[0]": str(line_7),

        # Taxes
        "f1_19[0]": str(ss_tax),
        "f1_20[0]": str(medicare_tax),

        # FINAL SE TAX
        "f1_21[0]": str(total_se_tax),

        # Deduction
        "f1_22[0]": str(deduction)
    }

    for page in pdf.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'].to_unicode()
                    if key in data:
                        annot.update(PdfDict(V=str(data[key])))
                        annot.update(PdfDict(AP=''))

    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=True))

    PdfWriter().write(output_path, pdf)

def generate_schedule_c(person):
    income = person["freelance_income"]

    # Realistic expense ratio
    expense_ratio = random.uniform(0.2, 0.6)
    total_expenses = int(income * expense_ratio)

    advertising = int(total_expenses * 0.1)
    car_truck = int(total_expenses * 0.15)
    office = int(total_expenses * 0.2)
    repairs = int(total_expenses * 0.15)
    supplies = total_expenses - (advertising + car_truck + office + repairs)

    net_profit = income - total_expenses

    return {
        "income": income,
        "returns": 0,
        "cogs": 0,
        "other_income": 0,

        "advertising": advertising,
        "car_truck": car_truck,
        "office": office,
        "repairs": repairs,
        "supplies": supplies,

        "total_expenses": total_expenses,
        "net_profit": net_profit
    }

def generate_schedule_1(schedule_c):
    return {
        "business_income": schedule_c["net_profit"]
    }

def fake_ssn():
    return f"TEST-{random.randint(1000,9999)}"


def create_pdf(path, text_lines):
    c = canvas.Canvas(path)
    y = 800
    for line in text_lines:
        c.drawString(50, y, str(line))
        y -= 18
    c.save()

def generate_supporting_docs(base, person, schedule_c):

    docs = []

    # BANK STATEMENT
    if person["interest_income"] > 0:
        path = base + "/Client Summary/bank_statement.pdf"
        create_pdf(path, [
            "=== BANK STATEMENT ===",
            f"Account Holder: {person['name']}",
            "Bank: Chase Bank",
            "",
            f"Interest Earned: ${person['interest_income']}",
            "",
            "--- TAX REPORTING ---",
            "Schedule B → Form 1040 Line 2b"
        ])
        docs.append(path)

    # BROKERAGE
    if person["dividend_income"] > 0:
        path = base + "/Client Summary/brokerage.pdf"
        create_pdf(path, [
            "=== BROKERAGE STATEMENT ===",
            "Broker: Fidelity",
            f"Dividends: ${person['dividend_income']}",
            "",
            "--- TAX REPORTING ---",
            "Schedule B → Form 1040 Line 3b"
        ])
        docs.append(path)

    # INVOICE + EXPENSES
    if person["freelance_income"] > 0:
        invoice_path = base + "/Client Summary/invoice.pdf"
        create_pdf(invoice_path, [
            "=== INVOICE ===",
            f"Service: {person['occupation']}",
            f"Income: ${person['freelance_income']}",
            "",
            "--- TAX REPORTING ---",
            "Schedule C → Schedule 1 → Form 1040"
        ])
        docs.append(invoice_path)

        expense_path = base + "/Client Summary/expenses.pdf"
        create_pdf(expense_path, [
            "=== EXPENSE RECEIPTS ===",
            f"Advertising: ${schedule_c['advertising']}",
            f"Office: ${schedule_c['office']}",
            f"Repairs: ${schedule_c['repairs']}",
            f"Supplies: ${schedule_c['supplies']}",
            "",
            f"Total: ${schedule_c['total_expenses']}",
            "",
            "--- TAX REPORTING ---",
            "Schedule C Expenses"
        ])
        docs.append(expense_path)

    return docs

def create_document_index(base):

    create_pdf(base + "/Client Summary/document_index.pdf", [
        "=== DOCUMENT INDEX ===",
        "1. W-2 → Form 1040 Line 1",
        "2. 1099-INT → Schedule B → Line 2b",
        "3. 1099-DIV → Schedule B → Line 3b",
        "4. Invoice → Schedule C",
        "5. Expenses → Schedule C",
        "",
        "All documents are internally consistent."
    ])

def fill_schedule_c(template_path, output_path, person, sc):

    pdf = PdfReader(template_path)

    name = person["name"]
    ssn = person["ssn"].replace("-", "")

    business_name = person["employer"]
    business_desc = person["occupation"]
    address = f"{person['address']}, {person['city']}, {person['state']} {person['zip']}"
    ein = f"{random.randint(10,99)}-{random.randint(1000000,9999999)}"

    # ---- Calculations ----
    gross_receipts = sc["income"]                     # f1_10
    returns = sc["returns"]                           # f1_11
    net_sales = gross_receipts - returns              # (line confusion in your PDF)
    cogs = sc["cogs"]                                 # f1_13
    gross_profit = net_sales - cogs                   # f1_14
    other_income = sc["other_income"]                 # f1_15
    gross_income = gross_profit + other_income        # f1_16

    data = {
        # ---- Header ----
        "f1_1[0]": name,
        "f1_2[0]": ssn,
        "f1_3[0]": business_desc,
        "f1_5[0]": business_name,
        "f1_6[0]": ein,
        "f1_7[0]": address,

        # ---- Income ----
        "f1_10[0]": str(gross_receipts),
        "f1_11[0]": str(returns),
        "f1_13[0]": str(cogs),
        "f1_14[0]": str(gross_profit),
        "f1_15[0]": str(other_income),
        "f1_16[0]": str(gross_income),

        # ---- Expenses ----
        "f1_17[0]": str(sc["advertising"]),
        "f1_18[0]": str(sc["car_truck"]),
        "f1_28[0]": str(sc["office"]),
        "f1_32[0]": str(sc["repairs"]),
        "f1_33[0]": str(sc["supplies"]),
        "f1_41[0]": str(sc["total_expenses"]),
        "f1_42[0]": str(sc["net_profit"]),

        # Optional COGS repeat field
        "f2_8[0]": str(cogs),
    }

    for page in pdf.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'].to_unicode()
                    if key in data:
                        annot.update(PdfDict(V=str(data[key])))
                        annot.update(PdfDict(AP=''))

    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=True))

    PdfWriter().write(output_path, pdf)

def fill_schedule_1(template_path, output_path, person, s1):

    pdf = PdfReader(template_path)

    name = person["name"]
    ssn = person["ssn"].replace("-", "")

    business_income = s1["business_income"]

    data = {
        "f1_01[0]": name,
        "f1_02[0]": ssn,

        # Part I
        "f1_07[0]": str(business_income),   # Line 3 equivalent
        "f1_38[0]": str(business_income),   # Total additional income
    }

    for page in pdf.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'].to_unicode()
                    if key in data:
                        annot.update(PdfDict(V=str(data[key])))
                        annot.update(PdfDict(AP=''))

    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=True))

    PdfWriter().write(output_path, pdf)
# -------- 1040 FILL --------
def fill_1040_full(template_path, output_path, person, filing_status, tax_data, year):

    template = PdfReader(template_path)

    first_name = person["name"].split()[0]
    last_name = person["name"].split()[-1]

    # ✅ CONSISTENT ADDRESS
    address = person["address"]
    city = person["city"]
    state = person["state"]
    zip_code = person["zip"]

    if filing_status == "Married Filing Jointly":
        spouse_first = person["spouse_name"].split()[0]
        spouse_last = person["spouse_name"].split()[-1]
        spouse_ssn = person["spouse_ssn"].replace("-", "")
    else:
        spouse_first = ""
        spouse_last = ""
        spouse_ssn = ""

    children = person.get("children", [])

    def split_name(child):
        if child["name"]:
            parts = child["name"].split()
            return parts[0], parts[-1]
        return "", ""

    def get_child(i):
        return children[i] if i < len(children) else {"name": "", "ssn": ""}

    c1, c2, c3, c4 = get_child(0), get_child(1), get_child(2), get_child(3)

    c1f, c1l = split_name(c1)
    c2f, c2l = split_name(c2)
    c3f, c3l = split_name(c3)
    c4f, c4l = split_name(c4)

    total_wages = person["w2_income"]
    interest = person["interest_income"]
    dividends = person["dividend_income"]
    se_tax = tax_data.get("se_tax", 0)

    total_income = tax_data["total_income"]
    agi = tax_data["agi"]
    taxable_income = tax_data["taxable_income"]
    tax = tax_data["final_tax"]
    deduction = STANDARD_DEDUCTION_BY_YEAR[year][filing_status]
    total_income_display = total_wages + interest + dividends + (tax_data["total_income"] - total_wages - interest - dividends)

    data = {
        "f1_14[0]": first_name,
        "f1_15[0]": last_name,
        "f1_16[0]": person["ssn"].replace("-", ""),
        "f1_17[0]": spouse_first,
        "f1_18[0]": spouse_last,
        "f1_19[0]": spouse_ssn,
        "f1_20[0]": address,

        "f1_22[0]": city,
        "f1_23[0]": state,
        "f1_24[0]": zip_code,

        "f1_31[0]": c1f,
        "f1_32[0]": c2f,
        "f1_33[0]": c3f,
        "f1_34[0]": c4f,

        "f1_35[0]": c1l,
        "f1_36[0]": c2l,
        "f1_37[0]": c3l,
        "f1_38[0]": c4l,

        "f1_39[0]": c1["ssn"].replace("-", "") if c1["ssn"] else "",
        "f1_40[0]": c2["ssn"].replace("-", "") if c2["ssn"] else "",
        "f1_41[0]": c3["ssn"].replace("-", "") if c3["ssn"] else "",
        "f1_42[0]": c4["ssn"].replace("-", "") if c4["ssn"] else "",

        "f1_47[0]": str(round(total_wages)),
        "f1_48[0]": "0",
        "f1_49[0]": "0",
        "f1_51[0]": "0",
        "f1_52[0]": "0",
        "f1_53[0]": "0",
        "f1_54[0]": "Other",
        "f1_55[0]": "0",

        "f1_57[0]": str(round(total_income_display)),
        "f1_58[0]": "0",
        "f1_59[0]": str(round(interest)),
        "f1_60[0]": str(round(dividends)),
        "f1_61[0]": str(round(dividends)),

        "f1_72[0]": "0",
        "f1_73[0]": str(round(total_income)),
        "f1_74[0]": "0",
        "f1_75[0]": str(round(agi)),
        

        "f2_02[0]": str(round(deduction)),
        "f2_03[0]": "0",
        "f2_05[0]": str(round(deduction)),
        "f2_06[0]": str(round(taxable_income)),
        "f2_08[0]": str(round(tax)),
        "f2_15[0]": str(round(se_tax)),
        
        "f2_16[0]": str(round(tax)),  # TOTAL TAX
        

        "f2_17[0]": str(round(person["tax_withheld"])),
        "f2_18[0]": "0",
        "f2_19[0]": "0",
        "f2_20[0]": str(round(person["tax_withheld"])),

        "f2_24[0]": str(round(tax_data["ctc"])),
        "f2_25[0]": str(round(tax_data["eitc"])),  # ✅ EITC ADDED
        "f2_28[0]": str(round(tax_data["ctc"])),
        "f2_29[0]": str(round(person["tax_withheld"])),

        "f2_30[0]": str(round(max(0, tax_data["refund"]))),
        "f2_31[0]": str(round(max(0, tax_data["refund"]))),
        "f2_35[0]": str(round(abs(min(0, tax_data["refund"])))),

        "f2_40[0]": person["occupation"],
        "f2_42[0]": person["occupation"],

        "f2_48[0]": "ABC Tax Services",
        "f2_50[0]": "123 Finance Street, NY"
    }

    for page in template.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'].to_unicode()
                    if key in data:
                        annot.update(PdfDict(V=str(data[key])))
                        annot.update(PdfDict(AP=''))

    if template.Root.AcroForm:
        template.Root.AcroForm.update(PdfDict(NeedAppearances=True))

    PdfWriter().write(output_path, template)

def fill_schedule_b(template_path, output_path, person):

    pdf = PdfReader(template_path)

    name = person["name"]
    ssn = person["ssn"].replace("-", "")

    interest = round(person["interest_income"])
    dividends = round(person["dividend_income"])

    # Interest section
    interest_payer = fake.company()

    # Dividend section
    dividend_payer = fake.company()

    total_interest = interest
    excludable_interest = 0
    net_interest = total_interest - excludable_interest

    total_dividends = dividends

    data = {
        # Header
        "f1_01[0]": name,
        "f1_02[0]": ssn,

        # Interest section
        "f1_03[0]": interest_payer,
        "f1_04[0]": str(interest),

        "f1_31[0]": str(total_interest),
        "f1_32[0]": str(excludable_interest),
        "f1_33[0]": str(net_interest),

        # Dividend section
        "f1_34[0]": dividend_payer,
        "f1_35[0]": str(dividends),

        "f1_64[0]": str(total_dividends)
    }

    for page in pdf.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'].to_unicode()
                    if key in data:
                        annot.update(PdfDict(V=str(data[key])))
                        annot.update(PdfDict(AP=''))

    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=True))

    PdfWriter().write(output_path, pdf)

def fill_1099_div(template_path, output_path, person):

    pdf = PdfReader(template_path)

    payer_name = fake.company()
    payer_address = fake.address().replace("\n", " ")
    payer_tin = f"{random.randint(10,99)}-{random.randint(1000000,9999999)}"

    recipient_tin = person["ssn"].replace("-", "")
    recipient_name = person["name"]

    address = person["address"]
    city = person["city"]
    state = person["state"]
    zip_code = person["zip"]

    dividends = round(person["dividend_income"])

    # Simple realistic splits
    qualified_dividends = round(dividends * 0.7)
    capital_gain = round(dividends * 0.3)

    data = {
        "f1_2[0]": f"{payer_name}, {payer_address}",
        "f1_3[0]": payer_tin,
        "f1_4[0]": recipient_tin,
        "f1_5[0]": recipient_name,

        "f1_6[0]": address,
        "f1_7[0]": f"{city}, {state}, {zip_code}",

        "f1_8[0]": str(random.randint(10000000, 99999999)),

        "f1_9[0]": str(dividends),
        "f1_10[0]": str(qualified_dividends),
        "f1_11[0]": str(capital_gain),

        "f1_12[0]": "0",
        "f1_13[0]": "0",
        "f1_14[0]": "0",
        "f1_15[0]": "0",
        "f1_16[0]": "0",
        "f1_17[0]": "0",

        "f1_18[0]": "0",
        "f1_19[0]": "0",
        "f1_20[0]": "0",

        "f1_21[0]": "0",
        "f1_22[0]": "",

        "f1_23[0]": "0",
        "f1_24[0]": "0",
        "f1_25[0]": "0",
        "f1_26[0]": "0",

        "f1_27[0]": state,
        "f1_29[0]": str(random.randint(100000, 999999)),
        "f1_31[0]": "0"
    }

    for page in pdf.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'].to_unicode()
                    if key in data:
                        annot.update(PdfDict(V=str(data[key])))
                        annot.update(PdfDict(AP=''))

    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=True))

    PdfWriter().write(output_path, pdf)

# -------- OTHER CREDITS --------
def generate_other_credits(person):
    eitc = 0
    if person["w2_income"] < 60000:
        eitc = random.randint(500, 2000)
    return {"earned_income_tax_credit": eitc}


# -------- STATE TAX --------
def generate_state_tax(state, tax_data):
    if state in ["TX", "FL"]:
        return {"state": state, "has_income_tax": False}

    income = tax_data["total_income"]
    tax = int(income * 0.04)
    credit = random.randint(100, 1000)

    return {
        "state": state,
        "has_income_tax": True,
        "state_tax": tax,
        "credits": credit,
        "net_tax": tax - credit
    }

def fill_1099_int(template_path, output_path, person):

    pdf = PdfReader(template_path)

    payer_name = fake.company()
    payer_address = fake.address().replace("\n", " ")
    payer_tin = f"{random.randint(10,99)}-{random.randint(1000000,9999999)}"

    recipient_tin = person["ssn"].replace("-", "")
    recipient_name = person["name"]

    address = person["address"]
    city = person["city"]
    state = person["state"]
    zip_code = person["zip"]

    interest_income = round(person["interest_income"])

    data = {
        "f1_1[0]": f"{payer_name}, {payer_address}",
        "f1_2[0]": payer_tin,
        "f1_3[0]": recipient_tin,
        "f1_4[0]": recipient_name,

        "f1_5[0]": address,
        "f1_6[0]": f"{city}, {state}, {zip_code}",

        "f1_7[0]": str(random.randint(10000000, 99999999)),

        "f1_9[0]": str(interest_income),

        "f1_10[0]": "0",
        "f1_11[0]": "0",
        "f1_12[0]": "0",
        "f1_13[0]": "0",
        "f1_14[0]": "0",
        "f1_15[0]": "",
        "f1_16[0]": "0",
        "f1_17[0]": "0",

        "f1_22[0]": "",
        "f1_23[0]": state,
        "f1_25[0]": str(random.randint(100000, 999999)),
        "f1_27[0]": "0"
    }

    for page in pdf.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'].to_unicode()
                    if key in data:
                        annot.update(PdfDict(V=str(data[key])))
                        annot.update(PdfDict(AP=''))

    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=True))

    PdfWriter().write(output_path, pdf)

# -------- W2 --------
def fill_w2(template_path, output_path, person, state):
    pdf = PdfReader(template_path)

    ssn = person["ssn"].replace("-", "")
    employer_name = person["employer"]

    # ✅ CONSISTENT ADDRESS
    employer_address = person["address"]

    employer_ein = f"{random.randint(10,99)}-{random.randint(1000000,9999999)}"
    control_number = str(random.randint(10000, 99999))

    first_name = person["name"].split()[0]
    last_name = person["name"].split()[-1]

    wages = round(person["w2_income"])
    federal_tax = round(person["tax_withheld"])

    ss_wages = wages
    ss_tax = round(ss_wages * 0.062)
    state_id = f"{random.randint(100000,999999)}"
    state_wages = wages

    if state in ["TX", "FL"]:
        state_tax = 0
        local_wages = wages
        local_tax = 0
        locality = "N/A"
    else:
        state_tax = int(state_wages * {
    "CA": 0.05,
    "NY": 0.07,
    "IL": 0.0495
}.get(state, 0))
        local_wages = wages
        local_tax = round(local_wages * 0.01)
        locality = person["city"]

    data = {
        "f1_01[0]": ssn,
        "f1_02[0]": employer_ein,
        "f1_03[0]": f"{employer_name}, {employer_address}",
        "f1_04[0]": control_number,
        "f1_05[0]": first_name,
        "f1_06[0]": last_name,
        "f1_08[0]": employer_address,

        "f1_09[0]": str(wages),
        "f1_10[0]": str(federal_tax),

        "f1_11[0]": str(ss_wages),
        "f1_12[0]": str(ss_tax),

        "f1_32[0]": state_id,
        "f1_35[0]": str(state_wages),
        "f1_37[0]": str(state_tax),
        "f1_39[0]": str(local_wages),
        "f1_41[0]": str(local_tax),
        "f1_43[0]": locality,
    }

    for page in pdf.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'].to_unicode()
                    if key in data:
                        annot.update(PdfDict(V=str(data[key])))
                        annot.update(PdfDict(AP=''))

    if pdf.Root.AcroForm:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=True))

    PdfWriter().write(output_path, pdf)


# -------- PERSON --------
def generate_person(level):
    w2_income = random.randint(30000, 90000)

    address_full = fake.address().replace("\n", " ")
    city = fake.city()
    state = fake.state_abbr()
    zip_code = fake.zipcode()

    data = {
        "name": fake.name(),
        "ssn": fake_ssn(),
        "address": address_full,
        "city": city,
        "state": state,
        "zip": zip_code,
        "employer": fake.company(),
        "occupation": fake.job(),
        "w2_income": w2_income,
        "tax_withheld": int(w2_income * random.uniform(0.1, 0.25))
    }

    data["interest_income"] = random.randint(0, 2000)
    data["dividend_income"] = random.randint(0, 2000)
    data["freelance_income"] = random.randint(0, 10000)
    data["tax_credits"] = random.randint(0, 2000)
    data["children"] = [{
        "name": fake.name(),
        "ssn": fake_ssn(),
        "age": random.randint(1, 16)
    } for _ in range(random.randint(1, 3))]

    return data
def compute_federal_tax(income, filing_status):
    brackets = {
        "Single": [
            (11000, 0.10), (44725, 0.12), (95375, 0.22),
            (182100, 0.24), (231250, 0.32), (578125, 0.35), (float('inf'), 0.37)
        ],
        "Married Filing Jointly": [
            (22000, 0.10), (89450, 0.12), (190750, 0.22),
            (364200, 0.24), (462500, 0.32), (693750, 0.35), (float('inf'), 0.37)
        ],
        "Head of Household": [
            (15700, 0.10), (59850, 0.12), (95350, 0.22),
            (182100, 0.24), (231250, 0.32), (578100, 0.35), (float('inf'), 0.37)
        ]
    }

    tax = 0
    prev_limit = 0

    for limit, rate in brackets[filing_status]:
        if income > limit:
            tax += (limit - prev_limit) * rate
            prev_limit = limit
        else:
            tax += (income - prev_limit) * rate
            break

    return round(tax)

# -------- TAX --------
# -------- TAX --------
def calculate_tax(data, filing_status, year, eitc=0, schedule_c=None):

    # ---- Income ----
    business_income = schedule_c["net_profit"] if schedule_c else 0

    total_income = (
        data["w2_income"]
        + data["interest_income"]
        + data["dividend_income"]
        + business_income
    )

    # 🔥 ---- Schedule SE integration ----
    se_tax = 0
    se_deduction = 0

    if business_income > 0:
        se_income = round(business_income * 0.9235)
        se_tax = round(se_income * 0.153)       # 15.3%
        se_deduction = round(se_tax * 0.5)      # 50% deduction

    # 🔥 ---- AGI FIX ----
    agi = total_income - se_deduction

    # ---- Standard deduction ----
    deduction = STANDARD_DEDUCTION_BY_YEAR[year][filing_status]
    taxable_income = max(0, agi - deduction)

    # ---- Federal tax ----
    fed_tax = compute_federal_tax(taxable_income, filing_status)

    # ---- Credits ----
    ctc = len(data["children"]) * 2000
    total_credits = data["tax_credits"] + ctc

    # 🔥 ---- FINAL TAX (include SE tax) ----
    final_tax = max(0, fed_tax - total_credits) + se_tax

    # ---- Refund ----
    refund = data["tax_withheld"] - final_tax + eitc

    return {
        "total_income": total_income,
        "agi": agi,
        "taxable_income": taxable_income,
        "raw_tax": fed_tax,
        "se_tax": se_tax,                 # ✅ NEW
        "se_deduction": se_deduction,     # ✅ NEW
        "final_tax": final_tax,
        "refund": refund,
        "ctc": ctc,
        "eitc": eitc
    }


# -------- DATASET --------
def create_dataset(i, state, year, level):
    person = generate_person(level)
    person["state"] = state

    filing_status = random.choice(["Single", "Married Filing Jointly", "Head of Household"])
    

    if filing_status == "Married Filing Jointly":
        person["spouse_name"] = fake.name()
        person["spouse_ssn"] = fake_ssn()
    else:
        person["spouse_name"] = "N/A"
        person["spouse_ssn"] = ""

    other_credits = generate_other_credits(person)
    if person["freelance_income"] > 0:
       schedule_c = generate_schedule_c(person)
    else:
      schedule_c = {"net_profit": 0}

    

    schedule_1 = generate_schedule_1(schedule_c)

    tax_data = calculate_tax(person, filing_status, year, other_credits["earned_income_tax_credit"],schedule_c)
    state_data = generate_state_data(state, person, tax_data)
  
    
    base = f"dataset_{i}_{state}_{year}_{level}"
    os.makedirs(base + "/Client Summary", exist_ok=True)
    os.makedirs(base + "/Complete form", exist_ok=True)
    # 🔥 ADD HERE
    generate_supporting_docs(base, person, schedule_c)
    create_document_index(base)

    create_state_summary(
    base + "/Complete form/State_Summary.pdf",
    state_data
)
    create_client_summary(
    base + "/Client Summary/Client_Summary.pdf",
    person,
    tax_data,
    state_data,
    filing_status
)
 
    
    

    fill_1040_full(
        "templates/1040.pdf",
        base + "/Complete form/1040_real.pdf",
        person,
        filing_status,
        tax_data,
        year
    )

    fill_w2(
        "templates/fw2.pdf",
        base + "/Complete form/W2.pdf",
        person,
        state
    )
    fill_schedule_1(
    "templates/f1040s1.pdf",
    base + "/Complete form/Schedule_1.pdf",
    person,
    schedule_1
)

    # ✅ ONLY generate if interest exists
    if person["interest_income"] > 0:
       fill_1099_int(
        "templates/f1099int.pdf",
        base + "/Complete form/1099_INT.pdf",
        person
    )
       # ✅ ONLY generate if dividends exist
    if person["dividend_income"] > 0:
       fill_1099_div(
        "templates/f1099div.pdf",
        base + "/Complete form/1099_DIV.pdf",
        person
    )
       # ✅ Generate Schedule B only if needed
    if person["interest_income"] > 0 or person["dividend_income"] > 0:
       fill_schedule_b(
        "templates/f1040sb.pdf",
        base + "/Complete form/Schedule_B.pdf",
        person
    )
       

    if person["freelance_income"] > 0:
      fill_schedule_c(
        "templates/f1040sc.pdf",
        base + "/Complete form/Schedule_C.pdf",
        person,
        schedule_c
    )
    if person["freelance_income"] > 0:
      fill_schedule_se(
        "templates/f1040sse.pdf",
        base + "/Complete form/Schedule_SE.pdf",
        person,
        schedule_c
    )
      

      
i = 1

for _ in range(10):
    state = random.choice(states)
    year = random.choice(years)
    level = random.choice(levels)

    create_dataset(i, state, year, level)
    i += 1