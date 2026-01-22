import os
import dbf
import random
from faker import Faker
import datetime

fake = Faker('es_MX')

MOCK_DIR = os.path.join(os.getcwd(), 'mocks')
os.makedirs(MOCK_DIR, exist_ok=True)

def create_dbf(filename, field_specs, records):
    path = os.path.join(MOCK_DIR, filename)
    if os.path.exists(path):
        os.remove(path)

    print(f"Creating {filename}...")
    try:
        table = dbf.Table(path, field_specs, codepage='cp1252')
        table.open(mode=dbf.READ_WRITE)
        for record in records:
            table.append(record)
        table.close()
        print(f"Created {path} with {len(records)} records.")
    except Exception as e:
        print(f"Error creating {filename}: {e}")
        # Print the record that failed?
        # For now just raise to see the error
        raise e

def safe_str(val, length):
    return str(val)[:length]

def generate_data():
    # Helper for 2026 dates
    # We want mostly 2026, some 2025.
    def get_date():
        if random.random() > 0.1:
            return fake.date_between(start_date=datetime.date(2026, 1, 1), end_date=datetime.date(2026, 12, 31))
        else:
            return fake.date_between(start_date=datetime.date(2025, 1, 1), end_date=datetime.date(2025, 12, 31))

    # 1. Agentes
    print("Generating Agentes...")
    agentes_specs = 'NOM_AGE C(60); FALTA_AGE D; AREA_AGE C(20); EMAIL_AGE C(60); CVE_AGE N(5,0)'
    agentes_records = []
    agent_ids = []
    for _ in range(30):
        cve = random.randint(1, 9999) # Safe range for N(5,0)
        agent_ids.append(cve)
        agentes_records.append({
            'NOM_AGE': safe_str(fake.name(), 60),
            'FALTA_AGE': fake.date_object(),
            'AREA_AGE': random.choice(['VENTAS', 'PRODUCCION', 'LOGISTICA']),
            'EMAIL_AGE': safe_str(fake.email(), 60),
            'CVE_AGE': cve
        })
    create_dbf('agentes.dbf', agentes_specs, agentes_records)

    # 2. Clientes
    print("Generating Clientes...")
    clientes_specs = 'NOM_CTE C(60); CVE_CTE C(10)'
    clientes_records = []
    client_ids = []
    for i in range(100):
        cve = f"{i+1:05d}"
        client_ids.append(cve)
        clientes_records.append({
            'NOM_CTE': safe_str(fake.company(), 60),
            'CVE_CTE': cve
        })
    create_dbf('clientes.dbf', clientes_specs, clientes_records)

    # 3. Productos
    print("Generating Productos...")
    productos_specs = 'CSE_PROD C(10); DESC_PROD C(60); FACT_PESO N(10,4); UNI_MED C(5); SUB_CSE C(20); SUB_SUBCSE C(20); CVE_PROD C(20)'
    productos_records = []
    prod_ids = []
    classes = ['RESINA', 'MOLIDO', 'FINAL', 'OTRO']
    for i in range(100):
        cve = f"PROD-{i+1:04d}"
        prod_ids.append(cve)
        productos_records.append({
            'CSE_PROD': random.choice(classes),
            'DESC_PROD': safe_str(fake.sentence(nb_words=3), 60),
            'FACT_PESO': random.uniform(0.1, 50.0),
            'UNI_MED': random.choice(['KG', 'PZA', 'LT']),
            'SUB_CSE': 'GENERAL',
            'SUB_SUBCSE': 'GENERAL',
            'CVE_PROD': cve
        })
    create_dbf('producto.dbf', productos_specs, productos_records)

    # 4. Provedor
    print("Generating Provedor...")
    prov_specs = 'NOM_PROV C(60); CVE_PROV C(10)'
    prov_records = []
    prov_ids = []
    for i in range(30):
        cve = f"PROV-{i+1:04d}"
        prov_ids.append(cve)
        prov_records.append({
            'NOM_PROV': safe_str(fake.company(), 60),
            'CVE_PROV': cve
        })
    create_dbf('provedor.dbf', prov_specs, prov_records)

    # 5. Facturas
    print("Generating Facturas...")
    # UPDATED: MES C(20) -> we'll use "01" but schema keeps it C(20) or less. N(4,0) -> C(4) for AÑO.
    # Actually, if the code expects '01', C(20) is fine. AÑO N(4,0) was loading as float. We change to C(4) so it loads as string and matches '2026'.
    facturac_specs = 'CVE_FACTU C(10); NO_FAC C(10); CVE_CTE C(10); FALTA_FAC D; STATUS_FAC C(10); CVE_MON N(2,0); TIP_CAM N(10,4); PESOTOT N(10,2); CVE_AGE N(5,0); F_PAGO D; SUBT_FAC N(10,2); TOTAL_FAC N(10,2); DESCUENTO N(10,2); SALDO_FAC N(10,2); SALDO_FAC2 N(10,2); MES C(20); AÑO C(4)'
    facturad_specs = 'CVE_FACTU C(10); NO_FAC C(10); CSE_PROD C(10); CVE_PROD C(20); VALOR_PROD N(10,2); CANT_SURT N(10,2); SUBT_PROD N(10,2); DESCU_PROD N(10,2)'

    facturac_records = []
    facturad_records = []

    # Generate MORE invoices to ensure charts are populated
    for i in range(500):
        fact_id = f"F{i+1:05d}"
        cve_factu = 'A'
        no_fac = f"{i+1}"

        date = get_date()
        # USE NUMERIC STRING MONTH
        mes = f"{date.month:02d}"

        subtotal = 0

        num_items = random.randint(1, 5)
        for _ in range(num_items):
            prod = random.choice(productos_records)
            cant = round(random.uniform(1, 100), 2)
            price = round(random.uniform(10, 500), 2)
            line_sub = round(cant * price, 2)
            subtotal += line_sub

            facturad_records.append({
                'CVE_FACTU': cve_factu,
                'NO_FAC': no_fac,
                'CSE_PROD': prod['CSE_PROD'],
                'CVE_PROD': prod['CVE_PROD'],
                'VALOR_PROD': price,
                'CANT_SURT': cant,
                'SUBT_PROD': line_sub,
                'DESCU_PROD': 0
            })

        total = round(subtotal * 1.16, 2)

        facturac_records.append({
            'CVE_FACTU': cve_factu,
            'NO_FAC': no_fac,
            'CVE_CTE': random.choice(client_ids),
            'FALTA_FAC': date,
            'STATUS_FAC': 'Emitida',
            'CVE_MON': 1,
            'TIP_CAM': 1.0,
            'PESOTOT': round(random.uniform(10, 1000), 2),
            'CVE_AGE': random.choice(agent_ids),
            'F_PAGO': date + datetime.timedelta(days=30),
            'SUBT_FAC': subtotal,
            'TOTAL_FAC': total,
            'DESCUENTO': 0,
            'SALDO_FAC': 0 if random.random() > 0.3 else total,
            'SALDO_FAC2': 0,
            'MES': mes,
            'AÑO': str(date.year) # String
        })

    create_dbf('facturac.dbf', facturac_specs, facturac_records)
    create_dbf('facturad.dbf', facturad_specs, facturad_records)

    # 6. Creditos
    print("Generating Creditos...")
    creditos_specs = 'CVE_DDA C(1); TIP_NOT C(10); FECHA D; DESC_NOTA C(60); NO_CLIENTE C(10); NO_AGENTE N(5,0); NO_ESTADO C(10); SUBTOTAL N(10,2); SALDO N(10,2); CVE_FACTU C(10); NO_FAC C(10); CVE_MON N(2,0); TIP_CAM N(10,4); MES C(20); AÑO C(4); NO_NOTA N(10,0)'
    creditod_specs = 'CVE_PROD C(20); MEDIDA C(10); CANTIDAD N(10,2); VALOR_PROD N(10,2); TOT N(10,2); UNIDAD C(5); NEWMED C(10); NO_NOTA N(10,0)'

    creditos_records = []
    creditod_records = []

    # 50 Credit notes
    for i in range(50):
        no_nota = i + 1
        date = get_date()
        mes = f"{date.month:02d}"

        ref_inv = random.choice(facturac_records)

        creditos_records.append({
            'CVE_DDA': 'D',
            'TIP_NOT': 'Dev. Just.',
            'FECHA': date,
            'DESC_NOTA': safe_str(fake.sentence(), 60),
            'NO_CLIENTE': ref_inv['CVE_CTE'],
            'NO_AGENTE': ref_inv['CVE_AGE'],
            'NO_ESTADO': 'Aplicada',
            'SUBTOTAL': 100.0,
            'SALDO': 0.0,
            'CVE_FACTU': ref_inv['CVE_FACTU'],
            'NO_FAC': ref_inv['NO_FAC'],
            'CVE_MON': 1,
            'TIP_CAM': 1.0,
            'MES': mes,
            'AÑO': str(date.year),
            'NO_NOTA': no_nota
        })

        creditod_records.append({
            'CVE_PROD': 'PROD-0001',
            'MEDIDA': '',
            'CANTIDAD': 1,
            'VALOR_PROD': 100.0,
            'TOT': 100.0,
            'UNIDAD': 'PZA',
            'NEWMED': '',
            'NO_NOTA': no_nota
        })

    create_dbf('creditos.dbf', creditos_specs, creditos_records)
    create_dbf('creditod.dbf', creditod_specs, creditod_records)

    # 7. Comprapc
    print("Generating CompraPC...")
    comprapc_specs = 'F_ALTA_PED D; STATUS C(10); TOTAL_PED N(10,2); SUBT_PED N(10,2); FECH_ENT D; CVE_MON N(2,0); TIP_CAM N(10,4); MES C(20); AÑO C(4); LUGAR C(20); STATUS_AUT C(10); NO_PEDC C(20)'
    comprapd_specs = 'CVE_PROD C(20); CSE_PROD C(10); CANT_PROD N(10,2); VALOR_PROD N(10,2); STATUS1 C(1); CVE_PROV C(10); SALDO N(10,2); F_ENT D; UNIDAD C(5); NEW_MED C(10); NO_PEDC C(20)'

    comprapc_records = []
    comprapd_records = []

    for i in range(50):
        no_pedc = f"PO-{i+1}"
        date = get_date()
        mes = f"{date.month:02d}"

        subtotal = 0
        num_items = random.randint(1, 3)

        for _ in range(num_items):
             prod = random.choice(productos_records)
             cant = round(random.uniform(10, 100), 2)
             cost = round(random.uniform(5, 50), 2)
             line_tot = round(cant * cost, 2)
             subtotal += line_tot

             comprapd_records.append({
                 'CVE_PROD': prod['CVE_PROD'],
                 'CSE_PROD': prod['CSE_PROD'],
                 'CANT_PROD': cant,
                 'VALOR_PROD': cost,
                 'STATUS1': 'A',
                 'CVE_PROV': random.choice(prov_ids),
                 'SALDO': 0,
                 'F_ENT': date + datetime.timedelta(days=15),
                 'UNIDAD': prod['UNI_MED'],
                 'NEW_MED': '',
                 'NO_PEDC': no_pedc
             })

        comprapc_records.append({
            'F_ALTA_PED': date,
            'STATUS': 'Emitida',
            'TOTAL_PED': round(subtotal * 1.16, 2),
            'SUBT_PED': subtotal,
            'FECH_ENT': date + datetime.timedelta(days=15),
            'CVE_MON': 1,
            'TIP_CAM': 1.0,
            'MES': mes,
            'AÑO': str(date.year),
            'LUGAR': 'ALMACEN',
            'STATUS_AUT': 'AUT',
            'NO_PEDC': no_pedc
        })

    create_dbf('comprapc.dbf', comprapc_specs, comprapc_records)
    create_dbf('comprapd.dbf', comprapd_specs, comprapd_records)

    # 8. Comprafc
    print("Generating CompraFC...")
    comprafc_specs = 'NO_FACC C(20); CVE_PROV C(10); STATUS_FAC C(10); SALDO_FAC N(10,2); LUGAR C(20); CVE_MON N(2,0); TIP_CAM N(10,4); SALDO_FAC2 N(10,2); FECH_VENCI D'
    comprafd_specs = 'NO_FACC C(20); CVE_PROV C(10); CSE_PRDO C(10); CVE_PROD C(20); CANT_SURT N(10,2); VALOR_PROD N(10,2); SUBT_PROD N(10,2); UNIDAD C(5); NEW_MED C(10)'

    comprafc_records = []
    comprafd_records = []

    for i in range(50):
        no_facc = f"FACPROV-{i+1}"
        prov = random.choice(prov_ids)
        date = get_date()

        subtotal = 0
        num_items = random.randint(1,4)
        for _ in range(num_items):
            prod = random.choice(productos_records)
            cant = round(random.uniform(5, 50), 2)
            cost = round(random.uniform(5, 50), 2)
            line_sub = round(cant * cost, 2)
            subtotal += line_sub

            comprafd_records.append({
                'NO_FACC': no_facc,
                'CVE_PROV': prov,
                'CSE_PRDO': prod['CSE_PROD'],
                'CVE_PROD': prod['CVE_PROD'],
                'CANT_SURT': cant,
                'VALOR_PROD': cost,
                'SUBT_PROD': line_sub,
                'UNIDAD': prod['UNI_MED'],
                'NEW_MED': ''
            })

        comprafc_records.append({
            'NO_FACC': no_facc,
            'CVE_PROV': prov,
            'STATUS_FAC': 'Emitida',
            'SALDO_FAC': round(subtotal * 1.16, 2),
            'LUGAR': 'ALMACEN',
            'CVE_MON': 1,
            'TIP_CAM': 1.0,
            'SALDO_FAC2': 0,
            'FECH_VENCI': date + datetime.timedelta(days=30)
        })

    create_dbf('comprafc.dbf', comprafc_specs, comprafc_records)
    create_dbf('comprafd.dbf', comprafd_specs, comprafd_records)

    # 9. Existe
    print("Generating Existe...")
    existe_specs = 'CVE_PROD C(20); NEW_MED C(10); LUGAR C(20); EXISTENCIA N(10,2); FECH_UMOD D; LOTE C(20); FECH_LOTE D; COSTO_PROM N(10,2); COSTUEPEPS N(10,2)'
    existe_records = []

    for prod in productos_records:
        if random.random() > 0.2: # 80% have stock
             existe_records.append({
                 'CVE_PROD': prod['CVE_PROD'],
                 'NEW_MED': '',
                 'LUGAR': 'ALMACEN',
                 'EXISTENCIA': round(random.uniform(100, 5000), 2),
                 'FECH_UMOD': fake.date_this_year(),
                 'LOTE': f"LOTE-{random.randint(1000,9999)}",
                 'FECH_LOTE': fake.date_this_year(),
                 'COSTO_PROM': round(random.uniform(10, 100), 2),
                 'COSTUEPEPS': round(random.uniform(10, 100), 2)
             })

    create_dbf('existe.dbf', existe_specs, existe_records)

    # 10. Pedidoc
    print("Generating Pedidoc...")
    pedidoc_specs = 'CVE_CTE C(10); CVE_AGE N(5,0); F_ALTA_PED D; STATUS C(10); SUBT_PED N(10,2); OBSERVA C(60); CVE_MON N(2,0); TIP_CAM N(10,4); MES C(20); AÑO C(4); FECHA_ENT D; STATUS2 C(1); PESOTOT N(10,2); NO_PED C(20)'
    pedidod_specs = 'CVE_PROD C(20); CSE_PROD C(10); CANT_PROD N(10,2); VALOR_PROD N(10,2); FECHA_ENT D; STATUS1 C(1); SALDO N(10,2); UNIDAD C(5); NEW_MED C(10); STAT_PRO C(1); NO_PED C(20)'

    pedidoc_records = []
    pedidod_records = []

    for i in range(100):
        no_ped = f"P{i+1:05d}"
        client = random.choice(clientes_records)
        agent = random.choice(agentes_records)

        date = get_date()

        mes = f"{date.month:02d}"
        fecha_ent = date + datetime.timedelta(days=random.randint(5, 60))

        subtotal = 0
        num_items = random.randint(1, 5)

        for _ in range(num_items):
            prod = random.choice(productos_records)
            cant = round(random.uniform(10, 500), 2)
            price = round(random.uniform(50, 200), 2)
            line_val = round(cant * price, 2)
            subtotal += line_val

            saldo = cant if random.random() > 0.5 else 0
            status1 = '' if saldo > 0 else 'S'

            pedidod_records.append({
                'CVE_PROD': prod['CVE_PROD'],
                'CSE_PROD': prod['CSE_PROD'],
                'CANT_PROD': cant,
                'VALOR_PROD': price,
                'FECHA_ENT': fecha_ent,
                'STATUS1': status1,
                'SALDO': saldo,
                'UNIDAD': prod['UNI_MED'],
                'NEW_MED': '',
                'STAT_PRO': '',
                'NO_PED': no_ped
            })

        pedidoc_records.append({
            'CVE_CTE': client['CVE_CTE'],
            'CVE_AGE': agent['CVE_AGE'],
            'F_ALTA_PED': date,
            'STATUS': 'Original',
            'SUBT_PED': subtotal,
            'OBSERVA': safe_str(fake.sentence(), 60),
            'CVE_MON': 1,
            'TIP_CAM': 1.0,
            'MES': mes,
            'AÑO': str(date.year),
            'FECHA_ENT': fecha_ent,
            'STATUS2': '',
            'PESOTOT': round(random.uniform(100, 1000), 2),
            'NO_PED': no_ped
        })

    create_dbf('pedidoc.dbf', pedidoc_specs, pedidoc_records)
    create_dbf('pedidod.dbf', pedidod_specs, pedidod_records)

    # 11. Ordproc
    print("Generating Ordproc...")
    ordproc_specs = 'NO_ORDP C(10); FECH_ORDP D; CVE_COPR C(10); REN_COPR N(10,0); STATUS C(10); CTO_UNIT N(10,2); NO_OPRO N(10,0); DATOEST4 C(10); NEW_COPR C(10); UNCRES N(10,2)'
    ordproc_records = []

    for i in range(50):
        date = get_date()

        ordproc_records.append({
            'NO_ORDP': f"OP-{i+1}",
            'FECH_ORDP': date,
            'CVE_COPR': 'PROCESO',
            'REN_COPR': 1,
            'STATUS': 'Terminada',
            'CTO_UNIT': round(random.uniform(10, 100), 2),
            'NO_OPRO': i+1,
            'DATOEST4': '',
            'NEW_COPR': '',
            'UNCRES': round(random.uniform(100, 1000), 2)
        })

    create_dbf('ordproc.dbf', ordproc_specs, ordproc_records)

if __name__ == "__main__":
    generate_data()
