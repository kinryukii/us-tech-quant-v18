from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import traceback
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


STATUS_OK = "OK_V18_28A_R1_THEME_MAP_BOOTSTRAP_READY"
STATUS_WARN = "WARN_V18_28A_R1_THEME_MAP_BOOTSTRAP_REVIEW_NEEDED"
STATUS_FAIL = "FAIL_V18_28A_R1_THEME_MAP_BOOTSTRAP_ERROR"
MODE = "THEME_MAP_BOOTSTRAP_COVERAGE_UPGRADE"

CURRENT_CANDIDATES = "outputs/v18/candidates/V18_CURRENT_RANKED_CANDIDATES.csv"
THEME_MAP = "state/v18/reference/V18_TICKER_THEME_MAP.csv"
OUT_RESULT = "outputs/v18/candidates/V18_28A_R1_THEME_MAP_BOOTSTRAP_RESULT.csv"
OUT_REVIEW = "outputs/v18/candidates/V18_28A_R1_THEME_MAP_REVIEW_QUEUE.csv"
OUT_REPORT = "outputs/v18/read_center/V18_28A_R1_THEME_MAP_BOOTSTRAP_REPORT.md"
OUT_READ_FIRST = "outputs/v18/ops/V18_28A_R1_READ_FIRST.txt"

PROTECTED_FILES = [
    CURRENT_CANDIDATES,
    "state/v18/forward_test/V18_DAILY_SIGNAL_FREEZE_LEDGER.csv",
    "outputs/v18/factor_pack/V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv",
    "outputs/v18/technical_timing/V18_6A_CURRENT_TECHNICAL_TIMING.csv",
    "state/v18/rolling_coverage/V18_23B_ROLLING_SCAN_LEDGER.csv",
]
PROTECTED_DIRS = ["state/v18/price_cache"]

THEME_FIELDS = [
    "ticker",
    "company_name",
    "primary_theme",
    "secondary_theme",
    "industry_group",
    "exposure_tags",
    "role_bucket",
    "cyclicality_bucket",
    "volatility_bucket",
    "liquidity_bucket",
    "manual_review_required",
    "notes",
]

READ_FIRST_FIELDS = [
    "STATUS",
    "MODE",
    "RUN_ID",
    "CURRENT_RANKED_CANDIDATE_ROW_COUNT",
    "THEME_MAP_ROW_COUNT_BEFORE",
    "THEME_MAP_ROW_COUNT_AFTER",
    "UNKNOWN_PRIMARY_THEME_COUNT_BEFORE",
    "UNKNOWN_PRIMARY_THEME_COUNT_AFTER",
    "MANUAL_REVIEW_REQUIRED_COUNT_BEFORE",
    "MANUAL_REVIEW_REQUIRED_COUNT_AFTER",
    "FILLED_PRIMARY_THEME_COUNT",
    "FILLED_COMPANY_NAME_COUNT",
    "DUPLICATE_THEME_TICKER_COUNT_AFTER",
    "TOP_50_UNKNOWN_COUNT",
    "TOP_100_UNKNOWN_COUNT",
    "FORBIDDEN_MODIFIED",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
]

RESULT_FIELDS = [
    "ticker",
    "rank",
    "primary_theme_before",
    "primary_theme_after",
    "company_name_before",
    "company_name_after",
    "manual_review_required_before",
    "manual_review_required_after",
    "updated",
    "update_reason",
]

REVIEW_FIELDS = [
    "ticker",
    "rank",
    "composite_candidate_score",
    "company_name",
    "primary_theme",
    "secondary_theme",
    "role_bucket",
    "manual_review_required",
    "notes",
]


def r(
    company_name: str,
    primary_theme: str,
    secondary_theme: str,
    industry_group: str,
    exposure_tags: str,
    role_bucket: str,
    cyclicality_bucket: str,
    volatility_bucket: str,
    liquidity_bucket: str = "HIGH",
) -> Dict[str, str]:
    return {
        "company_name": company_name,
        "primary_theme": primary_theme,
        "secondary_theme": secondary_theme,
        "industry_group": industry_group,
        "exposure_tags": exposure_tags,
        "role_bucket": role_bucket,
        "cyclicality_bucket": cyclicality_bucket,
        "volatility_bucket": volatility_bucket,
        "liquidity_bucket": liquidity_bucket,
        "manual_review_required": "FALSE",
        "notes": "V18.28A-R1 high-confidence local ticker rulebook classification; no external fetch.",
    }


RULEBOOK: Dict[str, Dict[str, str]] = {
    "AAPL": r("Apple Inc.", "CONSUMER", "Consumer devices and services", "Consumer Electronics", "iphone;services;hardware", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "AA": r("Alcoa Corporation", "INDUSTRIAL", "Aluminum materials", "Metals", "aluminum;materials;commodity", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "HIGH"),
    "AAL": r("American Airlines Group Inc.", "TRANSPORTATION", "Airlines", "Airlines", "airline;travel", "TACTICAL_BETA", "CYCLICAL", "HIGH"),
    "ABR": r("Arbor Realty Trust Inc.", "OTHER", "Mortgage REIT", "Real Estate Finance", "reit;mortgage_credit", "NON_CORE", "CYCLICAL", "HIGH"),
    "ACLS": r("Axcelis Technologies Inc.", "SEMICONDUCTOR_EQUIPMENT", "Ion implantation equipment", "Semiconductor Equipment", "wafer_fab;semi_capex", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "ACM": r("AECOM", "INDUSTRIAL", "Infrastructure engineering", "Engineering Services", "infrastructure;engineering", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "ACMR": r("ACM Research Inc.", "SEMICONDUCTOR_EQUIPMENT", "Wafer cleaning equipment", "Semiconductor Equipment", "wafer_fab;china_semicap", "SPECULATIVE_SATELLITE", "CYCLICAL", "EXTREME"),
    "ADBE": r("Adobe Inc.", "SOFTWARE", "Creative and digital media software", "Application Software", "creative_cloud;software", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "ADMA": r("ADMA Biologics Inc.", "HEALTHCARE", "Biologics", "Biotechnology", "biologics;plasma", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "ADSK": r("Autodesk Inc.", "SOFTWARE", "Design software", "Application Software", "cad;bim;software", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "AEHR": r("Aehr Test Systems", "SEMICONDUCTOR_EQUIPMENT", "Semiconductor test and burn-in", "Semiconductor Equipment", "test_equipment;sic", "SPECULATIVE_SATELLITE", "CYCLICAL", "EXTREME"),
    "AEIS": r("Advanced Energy Industries Inc.", "SEMICONDUCTOR_EQUIPMENT", "Power and control systems", "Semiconductor Equipment", "process_power;semi_capex", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "AEVA": r("Aeva Technologies Inc.", "AI_INFRASTRUCTURE", "Lidar and sensing", "Autonomous Sensing", "lidar;autonomy", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "AFRM": r("Affirm Holdings Inc.", "FINTECH", "Buy-now-pay-later", "Consumer Finance", "bnpl;consumer_credit", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "AGX": r("Argan Inc.", "POWER_INFRASTRUCTURE", "Power plant construction", "Infrastructure Construction", "power_generation;construction", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH", "MEDIUM"),
    "ALAB": r("Astera Labs Inc.", "AI_INFRASTRUCTURE", "AI connectivity semiconductors", "Semiconductors", "ai_connectivity;pcie;datacenter", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "AMAT": r("Applied Materials Inc.", "SEMICONDUCTOR_EQUIPMENT", "Wafer fabrication equipment", "Semiconductor Equipment", "wafer_fab;semi_capex", "CORE_GROWTH", "CYCLICAL", "HIGH"),
    "AMC": r("AMC Entertainment Holdings Inc.", "CONSUMER", "Movie theaters", "Entertainment", "cinema;meme_beta", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "AMD": r("Advanced Micro Devices Inc.", "SEMICONDUCTOR", "AI and compute processors", "Semiconductors", "gpu;cpu;ai_compute", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "AMKR": r("Amkor Technology Inc.", "SEMICONDUCTOR", "Outsourced semiconductor assembly and test", "Semiconductor Services", "osat;advanced_packaging", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "AMZN": r("Amazon.com Inc.", "ECOMMERCE", "E-commerce and cloud", "Internet Retail", "ecommerce;aws;cloud", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "ANET": r("Arista Networks Inc.", "DATA_INFRASTRUCTURE", "Cloud networking", "Networking Equipment", "datacenter_networking;ai_networks", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "APH": r("Amphenol Corporation", "ELECTRONICS_SUPPLY_CHAIN", "Connectors and interconnect", "Electronic Components", "connectors;industrial_electronics", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "APLD": r("Applied Digital Corporation", "AI_INFRASTRUCTURE", "AI data centers", "Data Center Infrastructure", "ai_datacenter;hosting", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "APP": r("AppLovin Corporation", "SOFTWARE", "Adtech software", "Application Software", "adtech;mobile_ads", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "APO": r("Apollo Global Management Inc.", "FINTECH", "Alternative asset management", "Asset Management", "private_credit;alternatives", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "ARM": r("Arm Holdings plc", "SEMICONDUCTOR", "CPU IP and architecture", "Semiconductors", "cpu_ip;mobile;datacenter", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "ASML": r("ASML Holding N.V.", "SEMICONDUCTOR_EQUIPMENT", "Lithography equipment", "Semiconductor Equipment", "euv;lithography;semi_capex", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "AVGO": r("Broadcom Inc.", "SEMICONDUCTOR", "Networking semiconductors and software", "Semiconductors", "ai_networking;custom_silicon;software", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "AXON": r("Axon Enterprise Inc.", "SOFTWARE", "Public safety hardware and software", "Public Safety Technology", "public_safety;saas;devices", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "BABA": r("Alibaba Group Holding Limited", "ECOMMERCE", "China e-commerce and cloud", "Internet Retail", "china_internet;ecommerce;cloud", "TACTICAL_BETA", "HIGH_BETA_MACRO", "HIGH"),
    "BAC": r("Bank of America Corporation", "FINTECH", "Large bank", "Banking", "bank;rates;credit", "TACTICAL_BETA", "CYCLICAL", "MEDIUM"),
    "BALL": r("Ball Corporation", "CONSUMER", "Packaging", "Packaging", "beverage_cans;packaging", "NON_CORE", "CYCLICAL", "MEDIUM"),
    "BE": r("Bloom Energy Corporation", "POWER_INFRASTRUCTURE", "Fuel cells and distributed power", "Clean Power", "fuel_cell;distributed_power", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "BIDU": r("Baidu Inc.", "INTERNET_PLATFORM", "China search and AI", "Internet Services", "china_internet;search;ai", "TACTICAL_BETA", "HIGH_BETA_MACRO", "HIGH"),
    "BITF": r("Bitfarms Ltd.", "CRYPTO_BETA", "Bitcoin mining", "Crypto Mining", "bitcoin_mining;crypto", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "BKNG": r("Booking Holdings Inc.", "INTERNET_PLATFORM", "Online travel", "Online Travel", "ota;travel", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "BN": r("Brookfield Corporation", "FINTECH", "Alternative assets", "Asset Management", "infrastructure_assets;alternatives", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "BSX": r("Boston Scientific Corporation", "HEALTHCARE", "Medical devices", "Medical Devices", "medtech;cardiology", "CORE_GROWTH", "DEFENSIVE", "MEDIUM"),
    "BTDR": r("Bitdeer Technologies Group", "CRYPTO_BETA", "Bitcoin mining and hash infrastructure", "Crypto Mining", "bitcoin_mining;crypto", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "BW": r("Babcock & Wilcox Enterprises Inc.", "POWER_INFRASTRUCTURE", "Power and environmental equipment", "Power Equipment", "power_equipment;industrial", "SPECULATIVE_SATELLITE", "CYCLICAL", "EXTREME", "MEDIUM"),
    "BYND": r("Beyond Meat Inc.", "CONSUMER", "Plant-based food", "Packaged Food", "plant_based_food;consumer", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "CAMT": r("Camtek Ltd.", "SEMICONDUCTOR_EQUIPMENT", "Inspection and metrology", "Semiconductor Equipment", "inspection;metrology;advanced_packaging", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "CARR": r("Carrier Global Corporation", "INDUSTRIAL", "HVAC and building systems", "Building Products", "hvac;buildings", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "CART": r("Maplebear Inc.", "ECOMMERCE", "Grocery delivery marketplace", "Online Grocery", "instacart;delivery;marketplace", "SPECULATIVE_SATELLITE", "CYCLICAL", "HIGH"),
    "CDNS": r("Cadence Design Systems Inc.", "SOFTWARE", "Electronic design automation", "EDA Software", "eda;chip_design", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "CEG": r("Constellation Energy Corporation", "POWER_INFRASTRUCTURE", "Nuclear and power generation", "Electric Utilities", "nuclear;power;ai_power", "CORE_GROWTH", "DEFENSIVE", "MEDIUM"),
    "CHPT": r("ChargePoint Holdings Inc.", "POWER_INFRASTRUCTURE", "EV charging", "EV Infrastructure", "ev_charging;clean_energy", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "CHRW": r("C.H. Robinson Worldwide Inc.", "TRANSPORTATION", "Freight brokerage", "Logistics", "freight;logistics", "NON_CORE", "CYCLICAL", "MEDIUM"),
    "CIEN": r("Ciena Corporation", "DATA_INFRASTRUCTURE", "Optical networking", "Networking Equipment", "optical_networking;telecom", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "CIFR": r("Cipher Mining Inc.", "CRYPTO_BETA", "Bitcoin mining", "Crypto Mining", "bitcoin_mining;crypto", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "CLF": r("Cleveland-Cliffs Inc.", "INDUSTRIAL", "Steel", "Metals", "steel;autos;commodity", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "HIGH"),
    "CLH": r("Clean Harbors Inc.", "INDUSTRIAL", "Environmental services", "Environmental Services", "waste;industrial_services", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "CLSK": r("CleanSpark Inc.", "CRYPTO_BETA", "Bitcoin mining", "Crypto Mining", "bitcoin_mining;crypto", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "CLS": r("Celestica Inc.", "AI_INFRASTRUCTURE", "AI server and electronics manufacturing", "Electronic Manufacturing Services", "ai_servers;ems;datacenter", "CYCLICAL_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "CMG": r("Chipotle Mexican Grill Inc.", "CONSUMER", "Restaurants", "Restaurants", "fast_casual;restaurants", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "COHR": r("Coherent Corp.", "DATA_INFRASTRUCTURE", "Optical components", "Electronic Components", "optics;datacenter;photonics", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "COHU": r("Cohu Inc.", "SEMICONDUCTOR_EQUIPMENT", "Semiconductor test equipment", "Semiconductor Equipment", "test_equipment;handlers", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "CORZ": r("Core Scientific Inc.", "CRYPTO_BETA", "Bitcoin mining and HPC hosting", "Crypto Mining", "bitcoin_mining;hpc_hosting", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "CRDO": r("Credo Technology Group Holding Ltd.", "AI_INFRASTRUCTURE", "High-speed connectivity semiconductors", "Semiconductors", "ai_networking;serdes;connectivity", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "CRM": r("Salesforce Inc.", "SOFTWARE", "Enterprise CRM software", "Application Software", "crm;enterprise_saas", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "CRWD": r("CrowdStrike Holdings Inc.", "CYBERSECURITY", "Endpoint cybersecurity", "Cybersecurity Software", "endpoint_security;cloud_security", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "CRWV": r("CoreWeave Inc.", "AI_INFRASTRUCTURE", "AI cloud infrastructure", "Cloud Infrastructure", "gpu_cloud;ai_compute", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "CSCO": r("Cisco Systems Inc.", "DATA_INFRASTRUCTURE", "Networking equipment", "Networking Equipment", "networking;enterprise", "DEFENSIVE_HEDGE", "CYCLICAL", "LOW"),
    "CVNA": r("Carvana Co.", "ECOMMERCE", "Online used autos", "Online Auto Retail", "used_cars;ecommerce;consumer_credit", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "D": r("Dominion Energy Inc.", "DEFENSIVE", "Regulated utility", "Electric Utilities", "utility;power", "DEFENSIVE_HEDGE", "DEFENSIVE", "LOW"),
    "DBVT": r("DBV Technologies S.A.", "HEALTHCARE", "Biotechnology", "Biotechnology", "allergy_immunotherapy;biotech", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME", "MEDIUM"),
    "DDOG": r("Datadog Inc.", "SOFTWARE", "Observability software", "Infrastructure Software", "observability;cloud_monitoring", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "DELL": r("Dell Technologies Inc.", "AI_INFRASTRUCTURE", "Servers and enterprise hardware", "Technology Hardware", "ai_servers;enterprise_hardware", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "ECL": r("Ecolab Inc.", "INDUSTRIAL", "Water hygiene and services", "Specialty Chemicals", "water;hygiene;industrial_services", "CORE_GROWTH", "DEFENSIVE", "LOW"),
    "ENTG": r("Entegris Inc.", "SEMICONDUCTOR_EQUIPMENT", "Semiconductor materials and filtration", "Semiconductor Materials", "semi_materials;filtration", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "ETN": r("Eaton Corporation plc", "POWER_INFRASTRUCTURE", "Electrical equipment", "Electrical Equipment", "electrification;grid;datacenter_power", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "ETR": r("Entergy Corporation", "DEFENSIVE", "Regulated utility", "Electric Utilities", "utility;power", "DEFENSIVE_HEDGE", "DEFENSIVE", "LOW"),
    "FCNCA": r("First Citizens BancShares Inc.", "FINTECH", "Banking", "Banking", "bank;credit", "TACTICAL_BETA", "CYCLICAL", "MEDIUM"),
    "FIX": r("Comfort Systems USA Inc.", "POWER_INFRASTRUCTURE", "Mechanical and electrical contracting", "Construction Services", "datacenter_power;hvac;construction", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "FLEX": r("Flex Ltd.", "ELECTRONICS_SUPPLY_CHAIN", "Electronics manufacturing services", "Electronic Manufacturing Services", "ems;hardware_supply_chain", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "FLR": r("Fluor Corporation", "INDUSTRIAL", "Engineering and construction", "Engineering Construction", "infrastructure;construction", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "FN": r("Fabrinet", "DATA_INFRASTRUCTURE", "Optical and precision manufacturing", "Electronic Manufacturing Services", "optical_components;ems", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "FORM": r("FormFactor Inc.", "SEMICONDUCTOR_EQUIPMENT", "Probe cards and test interfaces", "Semiconductor Equipment", "probe_cards;test", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "GEV": r("GE Vernova Inc.", "POWER_INFRASTRUCTURE", "Power generation and grid equipment", "Electrical Equipment", "grid;gas_power;electrification", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "GLW": r("Corning Incorporated", "ELECTRONICS_SUPPLY_CHAIN", "Glass and optical materials", "Electronic Components", "glass;fiber;display", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "GNRC": r("Generac Holdings Inc.", "POWER_INFRASTRUCTURE", "Backup power equipment", "Electrical Equipment", "backup_power;generators", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "GOOGL": r("Alphabet Inc.", "INTERNET_PLATFORM", "Search, ads, cloud and AI", "Internet Services", "search_ads;cloud;ai", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "HOOD": r("Robinhood Markets Inc.", "FINTECH", "Brokerage and crypto trading", "Capital Markets", "brokerage;crypto;retail_trading", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "HIGH"),
    "HPE": r("Hewlett Packard Enterprise Co.", "AI_INFRASTRUCTURE", "Servers and enterprise infrastructure", "Technology Hardware", "servers;networking;ai_infrastructure", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "HTZ": r("Hertz Global Holdings Inc.", "TRANSPORTATION", "Car rental", "Rental Services", "travel;fleet;autos", "TACTICAL_BETA", "CYCLICAL", "EXTREME"),
    "HUBB": r("Hubbell Incorporated", "POWER_INFRASTRUCTURE", "Electrical and utility products", "Electrical Equipment", "grid;electrification", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "ICHR": r("Ichor Holdings Ltd.", "SEMICONDUCTOR_EQUIPMENT", "Semiconductor fluid delivery subsystems", "Semiconductor Equipment", "wafer_fab_subsystems;semi_capex", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "IGV": r("iShares Expanded Tech-Software Sector ETF", "SOFTWARE", "Software ETF", "ETF", "software_etf", "TACTICAL_BETA", "SECULAR_GROWTH", "MEDIUM"),
    "INTC": r("Intel Corporation", "SEMICONDUCTOR", "Processors and foundry", "Semiconductors", "cpu;foundry", "TACTICAL_BETA", "CYCLICAL", "HIGH"),
    "IREN": r("IREN Limited", "CRYPTO_BETA", "Bitcoin mining and AI data centers", "Crypto Mining", "bitcoin_mining;ai_datacenter", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "IRDM": r("Iridium Communications Inc.", "DATA_INFRASTRUCTURE", "Satellite communications", "Telecommunications", "satellite;communications", "NON_CORE", "CYCLICAL", "MEDIUM"),
    "IYW": r("iShares U.S. Technology ETF", "SOFTWARE", "Technology ETF", "ETF", "technology_etf", "TACTICAL_BETA", "SECULAR_GROWTH", "MEDIUM"),
    "JBL": r("Jabil Inc.", "ELECTRONICS_SUPPLY_CHAIN", "Electronics manufacturing services", "Electronic Manufacturing Services", "ems;hardware_supply_chain", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "KEYS": r("Keysight Technologies Inc.", "SEMICONDUCTOR_EQUIPMENT", "Electronic test and measurement", "Test Equipment", "test_measurement;electronics", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "KLAC": r("KLA Corporation", "SEMICONDUCTOR_EQUIPMENT", "Process control and inspection", "Semiconductor Equipment", "metrology;inspection;semi_capex", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "KLIC": r("Kulicke and Soffa Industries Inc.", "SEMICONDUCTOR_EQUIPMENT", "Semiconductor assembly equipment", "Semiconductor Equipment", "assembly_equipment;advanced_packaging", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "LITE": r("Lumentum Holdings Inc.", "DATA_INFRASTRUCTURE", "Optical components", "Electronic Components", "optical_components;datacenter", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "LPLA": r("LPL Financial Holdings Inc.", "FINTECH", "Wealth management platform", "Capital Markets", "wealth_management;broker_dealer", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "LRCX": r("Lam Research Corporation", "SEMICONDUCTOR_EQUIPMENT", "Wafer fabrication equipment", "Semiconductor Equipment", "etch;deposition;semi_capex", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "LSCC": r("Lattice Semiconductor Corporation", "SEMICONDUCTOR", "Low-power FPGAs", "Semiconductors", "fpga;industrial_auto", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "LYB": r("LyondellBasell Industries N.V.", "INDUSTRIAL", "Chemicals", "Chemicals", "chemicals;commodity", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "MEDIUM"),
    "LYFT": r("Lyft Inc.", "TRANSPORTATION", "Rideshare", "Rideshare", "mobility;rideshare", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "HIGH"),
    "MA": r("Mastercard Incorporated", "FINTECH", "Payments network", "Payments", "card_network;payments", "CORE_GROWTH", "SECULAR_GROWTH", "LOW"),
    "MCHP": r("Microchip Technology Inc.", "SEMICONDUCTOR", "Microcontrollers and analog chips", "Semiconductors", "mcu;analog;industrial", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "MCK": r("McKesson Corporation", "HEALTHCARE", "Drug distribution", "Healthcare Distribution", "pharma_distribution;healthcare_services", "DEFENSIVE_HEDGE", "DEFENSIVE", "LOW"),
    "MDB": r("MongoDB Inc.", "SOFTWARE", "Database software", "Infrastructure Software", "database;developer_platform", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "MELI": r("MercadoLibre Inc.", "ECOMMERCE", "Latin America e-commerce and fintech", "Internet Retail", "latam_ecommerce;payments", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "META": r("Meta Platforms Inc.", "INTERNET_PLATFORM", "Social platform and AI", "Internet Services", "social_ads;ai;metaverse", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "MKSI": r("MKS Instruments Inc.", "SEMICONDUCTOR_EQUIPMENT", "Process control and photonics", "Semiconductor Equipment", "process_control;photonics", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "MOD": r("Modine Manufacturing Company", "POWER_INFRASTRUCTURE", "Thermal management", "Thermal Management", "datacenter_cooling;thermal", "CYCLICAL_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "MOH": r("Molina Healthcare Inc.", "HEALTHCARE", "Managed care", "Managed Healthcare", "medicaid;managed_care", "DEFENSIVE_HEDGE", "DEFENSIVE", "MEDIUM"),
    "MPLX": r("MPLX LP", "ENERGY", "Midstream energy", "Midstream Energy", "pipelines;midstream", "DEFENSIVE_HEDGE", "COMMODITY_CYCLICAL", "MEDIUM"),
    "MPWR": r("Monolithic Power Systems Inc.", "SEMICONDUCTOR", "Power semiconductors", "Semiconductors", "power_management;analog", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "MRVL": r("Marvell Technology Inc.", "SEMICONDUCTOR", "Data infrastructure semiconductors", "Semiconductors", "ai_networking;storage;custom_silicon", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "MSFT": r("Microsoft Corporation", "SOFTWARE", "Cloud and software", "Software", "azure;ai;productivity", "CORE_GROWTH", "SECULAR_GROWTH", "LOW"),
    "MTZ": r("MasTec Inc.", "POWER_INFRASTRUCTURE", "Infrastructure construction", "Construction Services", "grid;fiber;energy_infrastructure", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "MTSI": r("MACOM Technology Solutions Holdings Inc.", "SEMICONDUCTOR", "RF and optical semiconductors", "Semiconductors", "rf;optical;datacenter", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "MU": r("Micron Technology Inc.", "SEMICONDUCTOR", "Memory semiconductors", "Semiconductors", "dram;nand;hbm", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "NET": r("Cloudflare Inc.", "CYBERSECURITY", "Edge network and security", "Infrastructure Software", "edge_network;zero_trust;cdn", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "NFLX": r("Netflix Inc.", "INTERNET_PLATFORM", "Streaming entertainment", "Streaming Media", "streaming;content", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "NI": r("NiSource Inc.", "DEFENSIVE", "Regulated utility", "Gas Utilities", "utility;gas", "DEFENSIVE_HEDGE", "DEFENSIVE", "LOW"),
    "NOW": r("ServiceNow Inc.", "SOFTWARE", "Workflow automation software", "Application Software", "workflow;enterprise_saas", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "NRG": r("NRG Energy Inc.", "POWER_INFRASTRUCTURE", "Power generation and retail energy", "Electric Utilities", "power_generation;retail_energy", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "MEDIUM"),
    "NTAP": r("NetApp Inc.", "DATA_INFRASTRUCTURE", "Enterprise storage", "Data Storage", "storage;hybrid_cloud", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "NTRA": r("Natera Inc.", "HEALTHCARE", "Genetic testing", "Diagnostics", "genomics;diagnostics", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "NU": r("Nu Holdings Ltd.", "FINTECH", "Digital banking", "Digital Banking", "latam_fintech;digital_bank", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "NUVB": r("Nuvation Bio Inc.", "HEALTHCARE", "Oncology biotechnology", "Biotechnology", "oncology;biotech", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "NVAX": r("Novavax Inc.", "HEALTHCARE", "Vaccines", "Biotechnology", "vaccines;biotech", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "NVDA": r("NVIDIA Corporation", "AI_INFRASTRUCTURE", "AI accelerators and platform", "Semiconductors", "gpu;ai_compute;cuda", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "NVT": r("nVent Electric plc", "POWER_INFRASTRUCTURE", "Electrical enclosures and systems", "Electrical Equipment", "electrification;datacenter_power", "CYCLICAL_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "NXPI": r("NXP Semiconductors N.V.", "SEMICONDUCTOR", "Auto and industrial semiconductors", "Semiconductors", "auto_semis;industrial", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "OC": r("Owens Corning", "INDUSTRIAL", "Building materials", "Building Products", "insulation;roofing;housing", "TACTICAL_BETA", "CYCLICAL", "MEDIUM"),
    "OKTA": r("Okta Inc.", "CYBERSECURITY", "Identity security", "Cybersecurity Software", "identity;zero_trust", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "OLPX": r("Olaplex Holdings Inc.", "CONSUMER", "Beauty products", "Personal Care", "beauty;consumer", "SPECULATIVE_SATELLITE", "CYCLICAL", "HIGH"),
    "ON": r("ON Semiconductor Corporation", "SEMICONDUCTOR", "Power and sensing semiconductors", "Semiconductors", "auto_semis;power;sic", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "OPCH": r("Option Care Health Inc.", "HEALTHCARE", "Home infusion services", "Healthcare Services", "home_infusion;healthcare_services", "CYCLICAL_GROWTH", "DEFENSIVE", "MEDIUM"),
    "ORCL": r("Oracle Corporation", "SOFTWARE", "Database and cloud software", "Software", "database;cloud;enterprise", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "PANW": r("Palo Alto Networks Inc.", "CYBERSECURITY", "Network and cloud security", "Cybersecurity Software", "network_security;cloud_security", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "PATH": r("UiPath Inc.", "SOFTWARE", "Automation software", "Application Software", "rpa;automation", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "PCOR": r("Procore Technologies Inc.", "SOFTWARE", "Construction management software", "Application Software", "construction_software;saas", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "PCT": r("PureCycle Technologies Inc.", "INDUSTRIAL", "Recycled plastics", "Specialty Materials", "recycling;plastics", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "PDD": r("PDD Holdings Inc.", "ECOMMERCE", "China e-commerce", "Internet Retail", "china_ecommerce;marketplace", "TACTICAL_BETA", "HIGH_BETA_MACRO", "HIGH"),
    "PFGC": r("Performance Food Group Company", "CONSUMER", "Food distribution", "Food Distribution", "foodservice;distribution", "NON_CORE", "CYCLICAL", "MEDIUM"),
    "PGNY": r("Progyny Inc.", "HEALTHCARE", "Fertility benefits", "Healthcare Services", "fertility;benefits", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "PI": r("Impinj Inc.", "SEMICONDUCTOR", "RFID semiconductors", "Semiconductors", "rfid;iot", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "PINS": r("Pinterest Inc.", "INTERNET_PLATFORM", "Social discovery advertising", "Internet Services", "social_ads;consumer_internet", "CYCLICAL_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "PLTR": r("Palantir Technologies Inc.", "SOFTWARE", "AI analytics software", "Application Software", "ai_software;analytics;government", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "PLUG": r("Plug Power Inc.", "ENERGY", "Hydrogen fuel cells", "Clean Energy", "hydrogen;fuel_cell", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "PM": r("Philip Morris International Inc.", "DEFENSIVE", "Tobacco", "Consumer Staples", "tobacco;staples", "DEFENSIVE_HEDGE", "DEFENSIVE", "LOW"),
    "POWL": r("Powell Industries Inc.", "POWER_INFRASTRUCTURE", "Electrical power equipment", "Electrical Equipment", "switchgear;power_distribution", "CYCLICAL_GROWTH", "SECULAR_GROWTH", "HIGH", "MEDIUM"),
    "PSTG": r("Pure Storage Inc.", "DATA_INFRASTRUCTURE", "Enterprise storage", "Data Storage", "flash_storage;data_infrastructure", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "PTGX": r("Protagonist Therapeutics Inc.", "HEALTHCARE", "Biotechnology", "Biotechnology", "biotech;immunology", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "PTON": r("Peloton Interactive Inc.", "CONSUMER", "Connected fitness", "Leisure Products", "fitness;subscription", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "PUMP": r("ProPetro Holding Corp.", "ENERGY", "Oilfield services", "Oilfield Services", "pressure_pumping;shale", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "HIGH"),
    "PWR": r("Quanta Services Inc.", "POWER_INFRASTRUCTURE", "Utility and infrastructure contracting", "Construction Services", "grid;utility_construction;energy_infra", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "PYPL": r("PayPal Holdings Inc.", "FINTECH", "Digital payments", "Payments", "payments;checkout", "TACTICAL_BETA", "SECULAR_GROWTH", "MEDIUM"),
    "QCOM": r("QUALCOMM Incorporated", "SEMICONDUCTOR", "Mobile and edge semiconductors", "Semiconductors", "mobile_semis;edge_ai", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "QQQ": r("Invesco QQQ Trust", "SOFTWARE", "Nasdaq 100 ETF", "ETF", "mega_cap_growth;technology_etf", "TACTICAL_BETA", "SECULAR_GROWTH", "MEDIUM"),
    "QS": r("QuantumScape Corporation", "ENERGY", "Solid-state batteries", "Battery Technology", "battery;ev", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "QSR": r("Restaurant Brands International Inc.", "CONSUMER", "Restaurants", "Restaurants", "quick_service;restaurants", "NON_CORE", "CYCLICAL", "MEDIUM"),
    "RDDT": r("Reddit Inc.", "INTERNET_PLATFORM", "Social platform", "Internet Services", "social_media;ads;community", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "RH": r("RH", "CONSUMER", "Luxury home furnishings", "Specialty Retail", "furniture;housing", "TACTICAL_BETA", "CYCLICAL", "HIGH"),
    "RIOT": r("Riot Platforms Inc.", "CRYPTO_BETA", "Bitcoin mining", "Crypto Mining", "bitcoin_mining;crypto", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "RKT": r("Rocket Companies Inc.", "FINTECH", "Mortgage origination", "Consumer Finance", "mortgage;rates", "TACTICAL_BETA", "HIGH_BETA_MACRO", "HIGH"),
    "RNG": r("RingCentral Inc.", "SOFTWARE", "Cloud communications", "Application Software", "ucaas;communications_software", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "ROKU": r("Roku Inc.", "INTERNET_PLATFORM", "Streaming platform", "Streaming Media", "ctv_ads;streaming", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "HIGH"),
    "RTX": r("RTX Corporation", "INDUSTRIAL", "Aerospace and defense", "Aerospace Defense", "defense;aerospace", "DEFENSIVE_HEDGE", "CYCLICAL", "LOW"),
    "RVMD": r("Revolution Medicines Inc.", "HEALTHCARE", "Oncology biotechnology", "Biotechnology", "oncology;biotech", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "SANM": r("Sanmina Corporation", "ELECTRONICS_SUPPLY_CHAIN", "Electronics manufacturing services", "Electronic Manufacturing Services", "ems;hardware_supply_chain", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "SATS": r("EchoStar Corporation", "DATA_INFRASTRUCTURE", "Satellite communications", "Telecommunications", "satellite;wireless", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "HIGH"),
    "SCCO": r("Southern Copper Corporation", "INDUSTRIAL", "Copper mining", "Metals", "copper;mining;commodity", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "HIGH"),
    "SCHW": r("Charles Schwab Corporation", "FINTECH", "Brokerage and wealth", "Capital Markets", "brokerage;wealth;rates", "TACTICAL_BETA", "CYCLICAL", "MEDIUM"),
    "SE": r("Sea Limited", "INTERNET_PLATFORM", "Gaming, e-commerce and fintech", "Internet Services", "gaming;ecommerce;fintech", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "HIGH"),
    "SEI": r("SolarEdge Technologies Inc.", "ENERGY", "Solar power electronics", "Clean Energy", "solar;inverters", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "SFM": r("Sprouts Farmers Market Inc.", "CONSUMER", "Grocery retail", "Food Retail", "grocery;consumer_staples", "DEFENSIVE_HEDGE", "DEFENSIVE", "MEDIUM"),
    "SFIX": r("Stitch Fix Inc.", "ECOMMERCE", "Online apparel retail", "Online Retail", "apparel;ecommerce", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "SHOP": r("Shopify Inc.", "ECOMMERCE", "Merchant commerce platform", "Application Software", "ecommerce_enablement;payments", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "SHW": r("Sherwin-Williams Company", "CONSUMER", "Paint and coatings", "Building Products", "paint;housing", "CORE_GROWTH", "CYCLICAL", "LOW"),
    "SITM": r("SiTime Corporation", "SEMICONDUCTOR", "Precision timing semiconductors", "Semiconductors", "timing_chips;analog", "SPECULATIVE_SATELLITE", "CYCLICAL", "HIGH"),
    "SMCI": r("Super Micro Computer Inc.", "AI_INFRASTRUCTURE", "AI servers", "Technology Hardware", "ai_servers;datacenter", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "SMH": r("VanEck Semiconductor ETF", "SEMICONDUCTOR", "Semiconductor ETF", "ETF", "semiconductor_etf", "TACTICAL_BETA", "CYCLICAL", "HIGH"),
    "SMTC": r("Semtech Corporation", "SEMICONDUCTOR", "Analog and mixed-signal semiconductors", "Semiconductors", "analog;iot;connectivity", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "SNDK": r("SanDisk Corporation", "SEMICONDUCTOR", "Flash storage", "Semiconductors", "nand;storage", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "SNOW": r("Snowflake Inc.", "SOFTWARE", "Cloud data platform", "Infrastructure Software", "data_cloud;analytics", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "SNPS": r("Synopsys Inc.", "SOFTWARE", "Electronic design automation", "EDA Software", "eda;chip_design", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "SOXL": r("Direxion Daily Semiconductor Bull 3X Shares", "SEMICONDUCTOR", "Leveraged semiconductor ETF", "ETF", "leveraged_semiconductor_etf", "TACTICAL_BETA", "HIGH_BETA_MACRO", "EXTREME"),
    "SOXX": r("iShares Semiconductor ETF", "SEMICONDUCTOR", "Semiconductor ETF", "ETF", "semiconductor_etf", "TACTICAL_BETA", "CYCLICAL", "HIGH"),
    "SPOT": r("Spotify Technology S.A.", "INTERNET_PLATFORM", "Audio streaming", "Streaming Media", "music_streaming;ads", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "SPY": r("SPDR S&P 500 ETF Trust", "DEFENSIVE", "Broad market ETF", "ETF", "sp500;market_beta", "DEFENSIVE_HEDGE", "CYCLICAL", "MEDIUM"),
    "STM": r("STMicroelectronics N.V.", "SEMICONDUCTOR", "Auto and industrial semiconductors", "Semiconductors", "auto_semis;industrial;sic", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "STX": r("Seagate Technology Holdings plc", "DATA_INFRASTRUCTURE", "Data storage", "Data Storage", "hdd;storage", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "TEAM": r("Atlassian Corporation", "SOFTWARE", "Collaboration and developer software", "Application Software", "developer_tools;collaboration", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "TER": r("Teradyne Inc.", "SEMICONDUCTOR_EQUIPMENT", "Automated test equipment", "Semiconductor Equipment", "ate;test_equipment", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "TIGR": r("UP Fintech Holding Limited", "FINTECH", "Online brokerage", "Capital Markets", "online_brokerage;china", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "TLN": r("Talen Energy Corporation", "POWER_INFRASTRUCTURE", "Power generation", "Independent Power Producer", "power_generation;ai_power", "CYCLICAL_GROWTH", "COMMODITY_CYCLICAL", "HIGH"),
    "TQQQ": r("ProShares UltraPro QQQ", "SOFTWARE", "Leveraged Nasdaq 100 ETF", "ETF", "leveraged_growth_etf", "TACTICAL_BETA", "HIGH_BETA_MACRO", "EXTREME"),
    "TSLA": r("Tesla Inc.", "CONSUMER", "Electric vehicles and energy", "Automobiles", "ev;autonomy;energy_storage", "TACTICAL_BETA", "HIGH_BETA_MACRO", "HIGH"),
    "TSM": r("Taiwan Semiconductor Manufacturing Company Limited", "SEMICONDUCTOR", "Semiconductor foundry", "Semiconductors", "foundry;advanced_nodes", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "TSEM": r("Tower Semiconductor Ltd.", "SEMICONDUCTOR", "Specialty semiconductor foundry", "Semiconductors", "specialty_foundry;analog", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "TTD": r("The Trade Desk Inc.", "SOFTWARE", "Adtech platform", "Application Software", "programmatic_ads;ctv", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "TTMI": r("TTM Technologies Inc.", "ELECTRONICS_SUPPLY_CHAIN", "Printed circuit boards", "Electronic Components", "pcb;aerospace;datacenter", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "TTWO": r("Take-Two Interactive Software Inc.", "CONSUMER", "Video games", "Gaming", "video_games;entertainment", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "TWLO": r("Twilio Inc.", "SOFTWARE", "Cloud communications software", "Application Software", "cpaas;communications_software", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "TWST": r("Twist Bioscience Corporation", "HEALTHCARE", "Synthetic biology", "Life Science Tools", "synthetic_biology;genomics", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "TXN": r("Texas Instruments Incorporated", "SEMICONDUCTOR", "Analog semiconductors", "Semiconductors", "analog;embedded", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "U": r("Unity Software Inc.", "SOFTWARE", "Game engine and real-time 3D software", "Application Software", "game_engine;3d_software", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "HIGH"),
    "UAL": r("United Airlines Holdings Inc.", "TRANSPORTATION", "Airlines", "Airlines", "airline;travel", "TACTICAL_BETA", "CYCLICAL", "HIGH"),
    "UBER": r("Uber Technologies Inc.", "TRANSPORTATION", "Mobility and delivery platform", "Rideshare Delivery", "rideshare;delivery;logistics", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "UNH": r("UnitedHealth Group Incorporated", "HEALTHCARE", "Managed care", "Managed Healthcare", "managed_care;healthcare_services", "DEFENSIVE_HEDGE", "DEFENSIVE", "LOW"),
    "UPST": r("Upstart Holdings Inc.", "FINTECH", "AI lending platform", "Consumer Finance", "ai_lending;consumer_credit", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "USFD": r("US Foods Holding Corp.", "CONSUMER", "Food distribution", "Food Distribution", "foodservice;distribution", "NON_CORE", "CYCLICAL", "MEDIUM"),
    "V": r("Visa Inc.", "FINTECH", "Payments network", "Payments", "card_network;payments", "CORE_GROWTH", "SECULAR_GROWTH", "LOW"),
    "VEEV": r("Veeva Systems Inc.", "SOFTWARE", "Life sciences cloud software", "Application Software", "life_sciences_saas;crm", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "VECO": r("Veeco Instruments Inc.", "SEMICONDUCTOR_EQUIPMENT", "Process equipment", "Semiconductor Equipment", "deposition;advanced_packaging", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "VIAV": r("Viavi Solutions Inc.", "DATA_INFRASTRUCTURE", "Network test and optical technology", "Communications Equipment", "network_test;optical;telecom", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "VIST": r("Vista Energy S.A.B. de C.V.", "ENERGY", "Oil and gas exploration", "Oil and Gas", "upstream_energy;latam", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "HIGH"),
    "VMC": r("Vulcan Materials Company", "INDUSTRIAL", "Construction aggregates", "Building Materials", "aggregates;infrastructure", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "VRT": r("Vertiv Holdings Co.", "AI_INFRASTRUCTURE", "Data center power and cooling", "Electrical Equipment", "datacenter_power;cooling;ai_infra", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
    "VST": r("Vistra Corp.", "POWER_INFRASTRUCTURE", "Power generation", "Independent Power Producer", "power_generation;ai_power", "CORE_GROWTH", "COMMODITY_CYCLICAL", "HIGH"),
    "WAB": r("Westinghouse Air Brake Technologies Corporation", "TRANSPORTATION", "Rail equipment", "Rail Equipment", "rail;industrial", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "WDC": r("Western Digital Corporation", "DATA_INFRASTRUCTURE", "Data storage", "Data Storage", "hdd;nand;storage", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "WDAY": r("Workday Inc.", "SOFTWARE", "Human capital and finance software", "Application Software", "hcm;finance_saas", "CORE_GROWTH", "SECULAR_GROWTH", "MEDIUM"),
    "WHR": r("Whirlpool Corporation", "CONSUMER", "Home appliances", "Consumer Durables", "appliances;housing", "TACTICAL_BETA", "CYCLICAL", "MEDIUM"),
    "WING": r("Wingstop Inc.", "CONSUMER", "Restaurants", "Restaurants", "quick_service;restaurants", "CORE_GROWTH", "CYCLICAL", "MEDIUM"),
    "WLK": r("Westlake Corporation", "INDUSTRIAL", "Chemicals and building products", "Chemicals", "chemicals;vinyls;housing", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "MEDIUM"),
    "WULF": r("TeraWulf Inc.", "CRYPTO_BETA", "Bitcoin mining", "Crypto Mining", "bitcoin_mining;crypto", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "EXTREME"),
    "WWD": r("Woodward Inc.", "INDUSTRIAL", "Aerospace and industrial controls", "Aerospace Industrial", "aerospace;controls", "CYCLICAL_GROWTH", "CYCLICAL", "MEDIUM"),
    "XENE": r("Xenon Pharmaceuticals Inc.", "HEALTHCARE", "Neurology biotechnology", "Biotechnology", "neurology;biotech", "SPECULATIVE_SATELLITE", "SECULAR_GROWTH", "EXTREME"),
    "XLF": r("Financial Select Sector SPDR Fund", "FINTECH", "Financial sector ETF", "ETF", "financials_etf", "TACTICAL_BETA", "CYCLICAL", "MEDIUM"),
    "XLK": r("Technology Select Sector SPDR Fund", "SOFTWARE", "Technology sector ETF", "ETF", "technology_etf", "TACTICAL_BETA", "SECULAR_GROWTH", "MEDIUM"),
    "XPO": r("XPO Inc.", "TRANSPORTATION", "Freight transportation", "Logistics", "ltl;freight", "CYCLICAL_GROWTH", "CYCLICAL", "HIGH"),
    "XYZ": r("Block Inc.", "FINTECH", "Payments and financial software", "Payments", "payments;square;cash_app", "SPECULATIVE_SATELLITE", "HIGH_BETA_MACRO", "HIGH"),
    "YPF": r("YPF Sociedad Anonima", "ENERGY", "Oil and gas", "Oil and Gas", "upstream_energy;argentina", "TACTICAL_BETA", "COMMODITY_CYCLICAL", "HIGH"),
    "Z": r("Zillow Group Inc.", "INTERNET_PLATFORM", "Real estate marketplace", "Internet Services", "real_estate_marketplace;housing", "TACTICAL_BETA", "CYCLICAL", "HIGH"),
    "ZG": r("Zillow Group Inc.", "INTERNET_PLATFORM", "Real estate marketplace", "Internet Services", "real_estate_marketplace;housing", "TACTICAL_BETA", "CYCLICAL", "HIGH"),
    "ZS": r("Zscaler Inc.", "CYBERSECURITY", "Cloud security", "Cybersecurity Software", "zero_trust;secure_access", "CORE_GROWTH", "SECULAR_GROWTH", "HIGH"),
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    if not path.exists():
        return [], []
    for enc in ("utf-8-sig", "utf-8", "cp932", "latin-1"):
        try:
            with path.open("r", encoding=enc, newline="", errors="replace") as handle:
                reader = csv.DictReader(handle)
                return [dict(row) for row in reader], list(reader.fieldnames or [])
        except Exception:
            continue
    raise RuntimeError(f"Unable to read CSV: {path}")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: Sequence[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def norm(value: object) -> str:
    return str(value or "").strip()


def ticker(value: object) -> str:
    return norm(value).upper()


def is_unknown(value: object) -> bool:
    return norm(value).upper() in {"", "UNKNOWN", "NAN", "NONE", "NULL"}


def bool_true(value: object) -> bool:
    return norm(value).upper() in {"TRUE", "T", "YES", "Y", "1"}


def to_int(value: object, default: int = 0) -> int:
    try:
        text = norm(value)
        return int(float(text)) if text else default
    except Exception:
        return default


def file_sig(path: Path) -> Tuple[int, int]:
    if not path.exists() or path.is_dir():
        return (-1, -1)
    stat = path.stat()
    return int(stat.st_mtime_ns), int(stat.st_size)


def tree_sig(root: Path) -> Dict[str, Tuple[int, int]]:
    if not root.exists():
        return {}
    return {str(path.relative_to(root)): file_sig(path) for path in root.rglob("*") if path.is_file()}


def protected_sig(root: Path) -> Dict[str, object]:
    sig: Dict[str, object] = {}
    for rel in PROTECTED_FILES:
        sig[rel] = file_sig(root / rel)
    for rel in PROTECTED_DIRS:
        sig[rel] = tree_sig(root / rel)
    return sig


def duplicate_count(rows: Sequence[Dict[str, str]]) -> int:
    counts = Counter(ticker(row.get("ticker")) for row in rows if ticker(row.get("ticker")))
    return sum(1 for count in counts.values() if count > 1)


def unknown_count(rows: Sequence[Dict[str, str]]) -> int:
    return sum(1 for row in rows if is_unknown(row.get("primary_theme")))


def manual_count(rows: Sequence[Dict[str, str]]) -> int:
    return sum(1 for row in rows if bool_true(row.get("manual_review_required")) or is_unknown(row.get("primary_theme")))


def normalize_theme_map(rows: Sequence[Dict[str, str]], candidate_rows: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    current_by_ticker = {ticker(row.get("ticker")): row for row in rows if ticker(row.get("ticker"))}
    normalized: List[Dict[str, str]] = []
    seen = set()
    for candidate in candidate_rows:
        t = ticker(candidate.get("ticker"))
        if not t or t in seen:
            continue
        seen.add(t)
        source = current_by_ticker.get(t, {})
        out = {field: norm(source.get(field)) for field in THEME_FIELDS}
        out["ticker"] = t
        if is_unknown(out.get("primary_theme")):
            out["primary_theme"] = "UNKNOWN"
        out["manual_review_required"] = "TRUE" if bool_true(out.get("manual_review_required")) or is_unknown(out.get("primary_theme")) else "FALSE"
        normalized.append(out)
    return normalized


def apply_rulebook(rows: List[Dict[str, str]], rank_map: Dict[str, Dict[str, str]]) -> Tuple[List[Dict[str, object]], int, int]:
    result_rows: List[Dict[str, object]] = []
    filled_theme = 0
    filled_name = 0
    for row in rows:
        t = ticker(row.get("ticker"))
        before_theme = norm(row.get("primary_theme")) or "UNKNOWN"
        before_name = norm(row.get("company_name"))
        before_manual = row.get("manual_review_required", "")
        updated_fields: List[str] = []
        rule = RULEBOOK.get(t)

        generated_note = norm(row.get("notes")).startswith("Seeded by V18.28A without external data") or norm(row.get("notes")).startswith("V18.28A-R1 high-confidence")
        preserve_manual = not is_unknown(row.get("primary_theme")) and not bool_true(row.get("manual_review_required")) and not generated_note
        if rule and not preserve_manual:
            for field in THEME_FIELDS:
                if field == "ticker":
                    continue
                if field == "manual_review_required":
                    continue
                replace_seed_note = field == "notes" and norm(row.get(field)).startswith("Seeded by V18.28A without external data")
                if is_unknown(row.get(field)) or norm(row.get(field)) == "" or replace_seed_note:
                    row[field] = rule.get(field, row.get(field, ""))
                    if field == "primary_theme":
                        filled_theme += 1
                    if field == "company_name":
                        filled_name += 1
                    updated_fields.append(field)
            if not is_unknown(row.get("primary_theme")):
                row["manual_review_required"] = "FALSE"
        if is_unknown(row.get("primary_theme")):
            row["primary_theme"] = "UNKNOWN"
            row["manual_review_required"] = "TRUE"
            if not row.get("notes"):
                row["notes"] = "No high-confidence local rulebook classification; manual review required."

        rank_row = rank_map.get(t, {})
        result_rows.append(
            {
                "ticker": t,
                "rank": rank_row.get("rank", ""),
                "primary_theme_before": before_theme,
                "primary_theme_after": row.get("primary_theme", ""),
                "company_name_before": before_name,
                "company_name_after": row.get("company_name", ""),
                "manual_review_required_before": before_manual,
                "manual_review_required_after": row.get("manual_review_required", ""),
                "updated": "TRUE" if updated_fields else "FALSE",
                "update_reason": ";".join(updated_fields),
            }
        )
    return result_rows, filled_theme, filled_name


def review_sort_key(row: Dict[str, object]) -> Tuple[int, int, str]:
    manual_first = 0 if bool_true(row.get("manual_review_required")) else 1
    rank = to_int(row.get("rank"), 999999)
    return manual_first, rank, ticker(row.get("ticker"))


def build_review_queue(theme_rows: Sequence[Dict[str, str]], rank_map: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for row in theme_rows:
        t = ticker(row.get("ticker"))
        rank_row = rank_map.get(t, {})
        rows.append(
            {
                "ticker": t,
                "rank": rank_row.get("rank", ""),
                "composite_candidate_score": rank_row.get("composite_candidate_score", ""),
                "company_name": row.get("company_name", ""),
                "primary_theme": row.get("primary_theme", ""),
                "secondary_theme": row.get("secondary_theme", ""),
                "role_bucket": row.get("role_bucket", ""),
                "manual_review_required": row.get("manual_review_required", ""),
                "notes": row.get("notes", ""),
            }
        )
    return sorted(rows, key=review_sort_key)


def top_unknown_count(theme_rows: Sequence[Dict[str, str]], rank_map: Dict[str, Dict[str, str]], top_n: int) -> int:
    ranked = sorted(theme_rows, key=lambda row: to_int(rank_map.get(ticker(row.get("ticker")), {}).get("rank"), 999999))
    return sum(1 for row in ranked[:top_n] if is_unknown(row.get("primary_theme")))


def table(rows: Sequence[Dict[str, object]], fields: Sequence[str], limit: int = 40) -> str:
    selected = list(rows[:limit])
    if not selected:
        return "_None._"
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join(["---"] * len(fields)) + " |"
    body = ["| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |" for row in selected]
    return "\n".join([header, sep] + body)


def write_read_first(path: Path, values: Dict[str, object]) -> None:
    write_text(path, "\n".join(f"{field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS) + "\n")


def rerun_r28a(root: Path) -> None:
    module_path = root / "scripts/v18/v18_28A_sector_theme_classification_audit.py"
    spec = importlib.util.spec_from_file_location("v18_28A_sector_theme_classification_audit", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load R28A audit script: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run(root)


def build_report(values: Dict[str, object], theme_rows: Sequence[Dict[str, str]], result_rows: Sequence[Dict[str, object]], review_rows: Sequence[Dict[str, object]]) -> str:
    counts = Counter(row.get("primary_theme", "UNKNOWN") or "UNKNOWN" for row in theme_rows)
    count_rows = [{"primary_theme": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
    changed = [row for row in result_rows if row.get("updated") == "TRUE"]
    unknown_review = [row for row in review_rows if bool_true(row.get("manual_review_required"))]
    lines = [
        "# V18.28A-R1 Theme Map Bootstrap Coverage Upgrade",
        "",
        "## Read First",
        "",
    ]
    lines.extend([f"- {field}: {values.get(field, '')}" for field in READ_FIRST_FIELDS])
    lines.extend(
        [
            "",
            "## Primary Theme Counts After",
            "",
            table(count_rows, ["primary_theme", "count"], 40),
            "",
            "## Updated Rows",
            "",
            table(changed, ["ticker", "rank", "primary_theme_before", "primary_theme_after", "company_name_after", "update_reason"], 80),
            "",
            "## Manual Review Queue Preview",
            "",
            table(unknown_review, REVIEW_FIELDS, 50),
            "",
            "## Safety",
            "",
            "- No external data fetch was performed.",
            "- Only state/v18/reference/V18_TICKER_THEME_MAP.csv was updated as reference metadata.",
            "- Existing non-UNKNOWN manual classifications were preserved.",
            "- Official decisions, trading state, signal freeze, price cache, factor pack, technical timing, and rolling coverage were not intentionally modified.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(root: Path) -> Dict[str, object]:
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    protected_before = protected_sig(root)

    candidate_rows, candidate_fields = read_csv(root / CURRENT_CANDIDATES)
    theme_rows_raw, _theme_fields = read_csv(root / THEME_MAP)
    if not candidate_rows:
        raise RuntimeError(f"No current ranked candidate rows found: {root / CURRENT_CANDIDATES}")
    if not theme_rows_raw:
        raise RuntimeError(f"No theme map rows found: {root / THEME_MAP}")
    if "ticker" not in candidate_fields:
        raise RuntimeError("Current ranked candidates missing ticker column")

    rank_map = {ticker(row.get("ticker")): row for row in candidate_rows if ticker(row.get("ticker"))}
    before_rows = normalize_theme_map(theme_rows_raw, candidate_rows)
    before_unknown = unknown_count(before_rows)
    before_manual = manual_count(before_rows)
    before_count = len(before_rows)

    after_rows = [dict(row) for row in before_rows]
    result_rows, filled_theme, filled_name = apply_rulebook(after_rows, rank_map)
    after_count = len(after_rows)
    after_unknown = unknown_count(after_rows)
    after_manual = manual_count(after_rows)
    dupes_after = duplicate_count(after_rows)

    if before_count != len(candidate_rows) or after_count != len(candidate_rows):
        raise RuntimeError("Theme map row count does not match current ranked candidate row count")

    write_csv(root / THEME_MAP, after_rows, THEME_FIELDS)
    review_rows = build_review_queue(after_rows, rank_map)
    write_csv(root / OUT_RESULT, result_rows, RESULT_FIELDS)
    write_csv(root / OUT_REVIEW, review_rows, REVIEW_FIELDS)

    rerun_r28a(root)
    forbidden_modified = protected_sig(root) != protected_before

    if after_count != len(candidate_rows):
        status = STATUS_FAIL
    elif dupes_after == 0 and after_unknown < before_unknown:
        status = STATUS_OK
    elif dupes_after == 0:
        status = STATUS_WARN
    else:
        status = STATUS_WARN

    values = {
        "STATUS": status,
        "MODE": MODE,
        "RUN_ID": run_id,
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": len(candidate_rows),
        "THEME_MAP_ROW_COUNT_BEFORE": before_count,
        "THEME_MAP_ROW_COUNT_AFTER": after_count,
        "UNKNOWN_PRIMARY_THEME_COUNT_BEFORE": before_unknown,
        "UNKNOWN_PRIMARY_THEME_COUNT_AFTER": after_unknown,
        "MANUAL_REVIEW_REQUIRED_COUNT_BEFORE": before_manual,
        "MANUAL_REVIEW_REQUIRED_COUNT_AFTER": after_manual,
        "FILLED_PRIMARY_THEME_COUNT": filled_theme,
        "FILLED_COMPANY_NAME_COUNT": filled_name,
        "DUPLICATE_THEME_TICKER_COUNT_AFTER": dupes_after,
        "TOP_50_UNKNOWN_COUNT": top_unknown_count(after_rows, rank_map, 50),
        "TOP_100_UNKNOWN_COUNT": top_unknown_count(after_rows, rank_map, 100),
        "FORBIDDEN_MODIFIED": "TRUE" if forbidden_modified else "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, build_report(values, after_rows, result_rows, review_rows))
    return values


def write_failure(root: Path, error: BaseException) -> None:
    values = {
        "STATUS": STATUS_FAIL,
        "MODE": MODE,
        "RUN_ID": dt.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "CURRENT_RANKED_CANDIDATE_ROW_COUNT": 0,
        "THEME_MAP_ROW_COUNT_BEFORE": 0,
        "THEME_MAP_ROW_COUNT_AFTER": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT_BEFORE": 0,
        "UNKNOWN_PRIMARY_THEME_COUNT_AFTER": 0,
        "MANUAL_REVIEW_REQUIRED_COUNT_BEFORE": 0,
        "MANUAL_REVIEW_REQUIRED_COUNT_AFTER": 0,
        "FILLED_PRIMARY_THEME_COUNT": 0,
        "FILLED_COMPANY_NAME_COUNT": 0,
        "DUPLICATE_THEME_TICKER_COUNT_AFTER": 0,
        "TOP_50_UNKNOWN_COUNT": 0,
        "TOP_100_UNKNOWN_COUNT": 0,
        "FORBIDDEN_MODIFIED": "FALSE",
        "OFFICIAL_DECISION_IMPACT": "NONE",
        "AUTO_TRADE": "DISABLED",
        "AUTO_SELL": "DISABLED",
    }
    write_read_first(root / OUT_READ_FIRST, values)
    write_text(root / OUT_REPORT, f"# V18.28A-R1 Theme Map Bootstrap Error\n\n```text\n{error}\n\n{traceback.format_exc()}\n```\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="V18.28A-R1 theme map bootstrap coverage upgrade.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        values = run(root)
        print(f"STATUS: {values['STATUS']}")
        print(f"READ_FIRST: {root / OUT_READ_FIRST}")
        return 0 if values["STATUS"] != STATUS_FAIL else 1
    except Exception as exc:
        write_failure(root, exc)
        print(f"STATUS: {STATUS_FAIL}")
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
