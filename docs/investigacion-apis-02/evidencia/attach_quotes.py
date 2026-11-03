from pathlib import Path
import subprocess, sys
ROOT = Path(r'C:/Users/aleja/Downloads/App Financiera')
SCRIPT = Path(r'C:/Users/aleja/AppData/Local/hermes/profiles/trabajos/skills/research/grounded-citations/scripts/sources.py')
LEDGER = ROOT / 'docs/investigacion-apis-02/10-citations-ledger.json'
SNIPPETS = ROOT / 'docs/investigacion-apis-02/evidencia/citas-literales.txt'
API = ROOT / 'docs/investigacion-apis-02/evidencia/fundfacts-demo-IE00B4L5Y983.json'
LICENSE = ROOT / 'docs/investigacion-apis-02/evidencia/esma_data_py-LICENSE.md'
quotes = {
 1: ('La base de datos de VDOS está fundamentada en la información diaria que nos propocionan directamente las entidades gestoras, tanto nacionales como internacionales, registros oficiales tales como la Comisión Nacional del Mercado de Valores (CNMV) y la Dirección General de Seguros.', SNIPPETS),
 2: ('0,000% Comisión de custodia n/a Gastos corrientes 0,940% Comisión de reembolso 0,000% Comisión de suscripción 0,000% Factsheet 27/02/2026', SNIPPETS),
 3: ('The response is one JSON document: identity and key facts, TER, the SRRI risk indicator, a rule-based profile (category, risk band, concentration, region and sector tilt), top holdings, sector / country / asset-allocation breakdowns, calendar and annualised returns, a monthly performance series, volatility, Sharpe ratio and max drawdown — read from the documents the fund house publishes and refreshed every 24 hours.', SNIPPETS),
 4: ('Each plan comes with a number of requests per calendar month (UTC). One request is counted per ISIN that receives an answer — found or not found — on GET /funds/{isin}, POST /funds, POST /portfolio and GET /overlap, whether the payload is served from the 24-hour store or loaded fresh.', SNIPPETS),
 5: ('Everything in Starter, plus 9,000 requests per month Portfolio look-through and holdings overlap (50 ISINs per call) Document extraction: any KID or factsheet to JSON White-label factsheets: your logo, no FundFacts branding Commercial use across your products', SNIPPETS),
 6: ('You may use the data inside your own applications, analyses and reports, including commercial ones. You may not resell or redistribute the raw dataset as a competing data feed, share API keys between organisations, or attempt to circumvent quotas.', SNIPPETS),
 7: ('"isin":"IE00B4L5Y983","name":"iShares Core MSCI World UCITS ETF","demo":true,"cached":true,"generatedAt":"2026-10-26T14:01:30.983+00:00","expiresAt":"2026-10-27T14:01:30.983Z","data":{"costs":{"exit":"0.00%","entry":"0.00%","riy1y":"0.20%","riyRhp":"0.20%","ongoing":"0.20%","totalCost1y":"20 USD","transaction":"0.00%","totalCostRhp":"180 USD"', API),
 8: ('We offer a wide range of comparison tools and various API interfaces including product data feeds.', SNIPPETS),
 9: ('You can access feeds in two ways: by downloading a CSV list, or by using Create-a-Feed to customize your selection.', SNIPPETS),
 10: ('This feature allows Partners to download a CSV list of the feeds they can see from either Advertisers they are joined to or Advertisers that allow Partners to promote their products before joining:', SNIPPETS),
 11: ('Cada vez que un usuario contrata un seguro, cambia su tarifa de Internet, abre una cuenta bancaria o contrata cualquier otro producto o servicio a través de Kelisto, le cobramos una comisión al proveedor que lo ofrece.', SNIPPETS),
 12: ('Rankia puede ganar una comisión cuando contratas un producto a través de un enlace en nuestra web. Esta comisión proviene del presupuesto de marketing de las entidades que hemos seleccionado para colaborar y no afecta al coste para tí del producto o servicio.', SNIPPETS),
 13: ('Para conseguir que todos los contenidos de esta web sean gratuitos necesitamos contar con la publicidad y patrocinios que aparecen en nuestras páginas.', SNIPPETS),
 14: ('Una de las mejores cuentas remuneradas de octubre de 2026 es la de Openbank! Ofrece un 3,25% TAE durante 12 meses, sin límite de saldo remunerado, sin comisiones y sin domiciliar la nómina. ¡Solo tienes que ser nuevo cliente y activar Bizum!', SNIPPETS),
 15: ('Easily gather & process consumer data to supercharge and automate underwriting, onboarding and verification flows', SNIPPETS),
 16: ('ESMA Registers system offers machine-to-machine (A2A) services, exposing a set of services for retrieval of data maintained in ESMA Registers to external systems/clients.', SNIPPETS),
 17: ('This section provides references to the registers and financial market data that ESMA compiled on the basis of notifications and data provided by the relevant national competent authorities (NCAs) and information collected through ESMA’s supervisory activities.', SNIPPETS),
 18: ('The esma_data_py package provides a robust toolkit designed to streamline the process of searching and downloading data from the ESMA (European Securities and Markets Authority) register.', SNIPPETS),
 19: ('EUROPEAN UNION PUBLIC LICENCE v. 1.2 EUPL © the European Union 2007, 2016', LICENSE),
}
for sid, (text, evidence) in quotes.items():
    cmd = [sys.executable, str(SCRIPT), '--ledger', str(LEDGER), 'quote', str(sid), '--text', text, '--from', str(evidence)]
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    print(result.stdout.strip() or result.stderr.strip())
    if result.returncode:
        raise SystemExit(f'quote failed for [{sid}] (exit {result.returncode})')
