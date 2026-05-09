"""
Seed script — populates the database with:
  - Companies from the real CAMU group Excel files
  - Departments per company
  - Employees from base-data.xlsx
  - One active pay period (current)
  - Default users (admin, hr, and one manager per company)

Run: python seed.py
"""

import sys
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import (
    User, UserRole, Company, Department, Employee,
    PayPeriod, ManagerDepartment
)
from auth import hash_password

Base.metadata.create_all(bind=engine)


# ── Company catalogue ──────────────────────────────────────────────────────

COMPANIES = [
    dict(short_name="CAMU",         sheet_name="CAMU",
         full_name="Constructora y Comercializadora CAMU S.A.S",
         nit="900.062.553-1"),
    dict(short_name="ALICANTE",     sheet_name="ALICANTE",
         full_name="Alicante Constructores S.A.S",
         nit="900.887.367-9"),
    dict(short_name="PROMOTORA",    sheet_name="PROMOTORA EL PROGRESO",
         full_name="Constructora y Promotora el Progreso S.A.S",
         nit="900.471.667-7"),
    dict(short_name="YULDANA",      sheet_name="YULDANA",
         full_name="Yuldana S.A.S",
         nit="900.572.420-9"),
    dict(short_name="CALICANTO",    sheet_name="CALICANTO",
         full_name="Calicanto Camu S.A.S",
         nit="901.584.242-1"),
    dict(short_name="QUIMBAYA",     sheet_name="DESARROLLOS_INMOBI_QUIMBAYA",
         full_name="Desarrollos Inmobiliarios Quimbaya S.A.S",
         nit=""),
    dict(short_name="SERVICOL",     sheet_name="SERVICOL",
         full_name="Servicol S.A.S",
         nit=""),
]


# ── Departments per company ────────────────────────────────────────────────

DEPARTMENTS = {
    "CAMU": [
        "PRESIDENCIA",
        "GERENCIA",
        "INNOVACIÓN Y NUEVOS PROYECTOS",
        "DESARROLLO DE NEGOCIOS",
        "DEPARTAMENTO TÉCNICO",
        "DIRECCIÓN DE OBRAS",
        "DIRECCIÓN DE CLIENTES",
        "MERCADEO",
        "TALENTO HUMANO",
        "DEPARTAMENTO CONTABLE",
        "SERVICIOS GENERALES ARMENIA / TALENTO HUMANO",
        "FINCA EL EDEN / GRAN CHAPARRAL",
        "SERVICIO AL CLIENTE ARMENIA",
        "SERVICIO AL CLIENTE MANIZALES",
        "POSTVENTA - ARMENIA",
        "OBRA BRASSIA / CONSTRUCTIVO",
    ],
    "ALICANTE": [
        "GERENCIA",
        "SERVICIO AL CLIENTE PEREIRA",
        "OBRA VIVARIUM / CONSTRUCTIVO",
        "POSTVENTA - ARMENIA",
    ],
    "PROMOTORA": [
        "DESARROLLO DE NEGOCIOS",
        "ACOMPAÑAMIENTO AL CLIENTE ARMENIA",
        "ACOMPAÑAMIENTO AL CLIENTE PEREIRA",
        "MERCADEO Y PUBLICIDAD",
        "DEPARTAMENTO CONTABLE",
        "COMERCIAL ARMENIA",
        "COMERCIAL PEREIRA",
        "COMERCIAL MANIZALES",
        "DIRECCIÓN DE OBRAS",
        "POSTVENTA - ARMENIA",
        "OBRA MILAN 170 / CONSTRUCTIVO",
        "OBRA PRADERA VIVA / CONSTRUCTIVO",
        "TALENTO HUMANO",
    ],
    "YULDANA": [
        "INNOVACIÓN Y NUEVOS PROYECTOS",
        "CENTRO COMERCIAL YULDANA / TALENTO HUMANO",
    ],
    "CALICANTO": [
        "DESARROLLO DE NEGOCIOS",
        "ACOMPAÑAMIENTO AL CLIENTE",
        "COMERCIAL ARMENIA",
        "DEPARTAMENTO CONTABLE",
        "OBRA CAVANNA / CONSTRUCTIVO",
        "OBRA TERRUM / CONSTRUCTIVO",
        "POSTVENTA - ARMENIA",
        "GESTIÓN TÉCNICA",
    ],
    "QUIMBAYA": [
        "GERENCIA",
    ],
    "SERVICOL": [
        "MERCADEO",
        "DEPARTAMENTO CONTABLE",
        "GESTIÓN TÉCNICA",
        "ACOMPAÑAMIENTO AL CLIENTE",
        "OBRA CAVANNA / CONSTRUCTIVO",
        "POSTVENTA - ARMENIA",
    ],
}


# ── Employee data extracted from base-data.xlsx + 26-02 Excel ─────────────
# Format: (full_name, cedula, internal_code, company_short, dept_name, project_code, cargo)

EMPLOYEES = [
    # ── CAMU ──
    ("Cesar Augusto Mejia Urrea",           "2867825",    "00.316.976", "CAMU",     "PRESIDENCIA",                          "ADMON OFICINA PPAL", "Presidente"),
    ("Clarena Mejia Giraldo",               "9697354961", "00.316.977", "CAMU",     "GERENCIA",                             "ADMON OFICINA PPAL", "Gerente"),
    ("Nelly Johana Galeano Diaz",           "2181241943", "00.316.981", "CAMU",     "INNOVACIÓN Y NUEVOS PROYECTOS",        "ADMON OFICINA PPAL", "Coordinador Transformación Digital"),
    ("Estefania Garcia Leguizamon",         "1958682846", "00.316.982", "CAMU",     "INNOVACIÓN Y NUEVOS PROYECTOS",        "ADMON OFICINA PPAL", ""),
    ("José Alejandro Mejia Giraldo",        "2719583",    "00.316.978", "CAMU",     "DESARROLLO DE NEGOCIOS",               "ADMON OFICINA PPAL", "Director Desarrollo de Negocios"),
    ("Claudia Piedad Castaño Gaitan",       "83197857",   "00.316.979", "CAMU",     "DESARROLLO DE NEGOCIOS",               "ADMON OFICINA PPAL", "Abogado"),
    ("Germán Alonso Castrillón Ramírez",    "21668732",   "00.316.921", "CAMU",     "DEPARTAMENTO TÉCNICO",                 "ADMON OFICINA PPAL", ""),
    ("Bibiana Hernandez Timote",            "89254563",   "00.316.928", "CAMU",     "DEPARTAMENTO TÉCNICO",                 "ADMON OFICINA PPAL", "Coordinador de Gestión Logística"),
    ("Mario Fernando Vallejo Arteaga",      "66629388",   "00.316.925", "CAMU",     "DEPARTAMENTO TÉCNICO",                 "ADMON OFICINA PPAL", "Coordinador de Presupuestos y Control de Costos"),
    ("Diana Milena Gil Hurtado",            "14265799",   "00.316.934", "CAMU",     "DIRECCIÓN DE OBRAS",                   "ADMON OFICINA PPAL", "Director de Obras"),
    ("Alina Esperanza Lopez Alzate",        "13999315",   "00.317.063", "CAMU",     "DIRECCIÓN DE CLIENTES",                "ADMON OFICINA PPAL", "Director de Clientes"),
    ("Wilmer Duarte Angulo",                "1402418010", "00.317.120", "CAMU",     "MERCADEO",                             "ADMON OFICINA PPAL", ""),
    ("Diana Carolina Betancourth Ceballos", "3585650756", "00.316.893", "CAMU",     "MERCADEO",                             "ADMON OFICINA PPAL", ""),
    ("Luz Marina Gomez Vargas",             "85329037",   "",           "CAMU",     "TALENTO HUMANO",                       "ADMON OFICINA PPAL", "Director de Talento Humano"),
    ("Juan Pablo Giraldo Bedoya",           "7635473142", "",           "CAMU",     "TALENTO HUMANO",                       "ADMON OFICINA PPAL", "Mensajero"),
    ("Jesus Elmer Zapata Granada",          "6241752544", "",           "CAMU",     "DEPARTAMENTO CONTABLE",                "ADMON OFICINA PPAL", "Director Contable y Financiero"),
    ("Yanince Diaz Cifuentes",              "89089901",   "",           "CAMU",     "DEPARTAMENTO CONTABLE",                "ADMON OFICINA PPAL", "Coordinador Comercial"),
    ("Adriana Cristina Portillo",           "47338124",   "",           "CAMU",     "SERVICIO AL CLIENTE ARMENIA",          "ADMON OFICINA PPAL", "Representante de ventas"),
    ("Erika Viviana Diaz Gaitan",           "4460967357", "",           "CAMU",     "SERVICIO AL CLIENTE ARMENIA",          "ADMON OFICINA PPAL", "Representante de Ventas"),
    ("Natalia Gil Gil",                     "8293453178", "00.316.916", "CAMU",     "SERVICIO AL CLIENTE ARMENIA",          "ADMON OFICINA PPAL", ""),
    ("Jhoan Alexis Pérez Castaño",          "55667651",   "00.316.897", "CAMU",     "SERVICIO AL CLIENTE MANIZALES",        "ADMON OFICINA PPAL", ""),
    ("Maria Lucelly Rubiano Lopez",         "47295260",   "00.317.150", "CAMU",     "SERVICIOS GENERALES ARMENIA / TALENTO HUMANO", "ADMON OFICINA PPAL", ""),
    ("Norbey Alberto Pineda Monrory",       "3608513",    "00.317.156", "CAMU",     "FINCA EL EDEN / GRAN CHAPARRAL",       "ADMON OFICINA PPAL", "Administrador de Finca"),
    ("Gloria Inés Rodriguez Hernández",     "8574149614", "00.317.155", "CAMU",     "FINCA EL EDEN / GRAN CHAPARRAL",       "ADMON OFICINA PPAL", "Auxiliar de Servicios Generales"),
    ("Maria Angelica Delgado Gutierrez",    "23718431",   "00.317.117", "CAMU",     "POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  ""),
    ("Arnulfo Mahecha Corrales",            "22448136",   "00.317.110", "CAMU",     "POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  "Pintor de Obra"),
    ("Efrain Montenegro Barreto",           "7374122",    "00.317.109", "CAMU",     "POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  "Oficial de Obra"),
    ("Camilo Herrera Restrepo",             "5710360983", "00.317.012", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Jhon Fredy Angarita Puerta",          "56164955",   "00.317.013", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Luz Mery Chilito Melo",               "91030736",   "00.317.017", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Héctor Andrés Cano Bernal",           "9776552803", "00.317.016", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Jesus David Medina Martinez",         "9256195745", "00.317.015", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Daner Durley Cerquera Piñarete",      "9928378856", "00.317.014", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Luis Fernando Correa Lopez",          "5918715",    "00.317.018", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Oscar Ivan Varela Ocampo",            "8995970241", "00.317.019", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Yesid José Ducuara Romero",           "4226067",    "00.317.020", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            ""),
    ("Carlos Arturo Hernandez Bermudez",    "4026113008", "00.317.021", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            "Ayudante Practico de Obra"),
    ("Natalia Castañeda Montealegre",       "9786748825", "00.317.022", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            "Inspector de Obra"),
    ("Oliverio Claros",                     "40587988",   "00.317.023", "CAMU",     "OBRA BRASSIA / CONSTRUCTIVO",          "BRASSIA",            "Oficial de Obra"),

    # ── ALICANTE ──
    ("Clarena Mejia Giraldo",               "9697354961", "00.316.977", "ALICANTE", "GERENCIA",                             "ADMON OFICINA PPAL", "Gerente"),
    ("Eber Julián Rendón Montoya",          "8615270538", "00.316.913", "ALICANTE", "SERVICIO AL CLIENTE PEREIRA",          "ADMON OFICINA PPAL", ""),
    ("Brisney Patricia Romero Gaviria",     "20709497",   "00.317.165", "ALICANTE", "OBRA VIVARIUM / CONSTRUCTIVO",         "VIVARIUM",           "Oficial de Obra"),
    ("Marco Tulio Ruiz Velez",              "41244663",   "00.317.115", "ALICANTE", "POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  ""),
    ("Brayan Andrei Torres Ducuara",        "4721519026", "00.317.114", "ALICANTE", "POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  ""),

    # ── PROMOTORA ──
    ("José Alejandro Mejia Giraldo",        "2719583",    "00.316.978", "PROMOTORA","DESARROLLO DE NEGOCIOS",               "ADMON OFICINA PPAL", "Director Desarrollo de Negocios"),
    ("Maridel Mateus Romero",               "61019678",   "00.316.980", "PROMOTORA","DESARROLLO DE NEGOCIOS",               "ADMON OFICINA PPAL", "Coordinador Desarrollo de Negocios"),
    ("Andrés Sánchez Henao",                "6488854841", "00.316.892", "PROMOTORA","ACOMPAÑAMIENTO AL CLIENTE ARMENIA",    "ADMON OFICINA PPAL", ""),
    ("Mary Luz Toro Naranjo",               "2566942273", "00.316.886", "PROMOTORA","ACOMPAÑAMIENTO AL CLIENTE PEREIRA",    "ADMON OFICINA PPAL", ""),
    ("Juan David Varón Guzmán",             "6884882440", "00.316.894", "PROMOTORA","MERCADEO Y PUBLICIDAD",                "ADMON OFICINA PPAL", ""),
    ("Luz Elena Rivera Carmona",            "38119557",   "00.317.064", "PROMOTORA","DEPARTAMENTO CONTABLE",                "DEPTO. CONTABLE FINA","Tesorera"),
    ("Karen Dayana Marin Taba",             "8173347748", "00.317.057", "PROMOTORA","DEPARTAMENTO CONTABLE",                "DEPTO. CONTABLE FINA","Coordinador Contable"),
    ("Santiago Arbeláez Bolívar",           "9896606039", "00.317.061", "PROMOTORA","DEPARTAMENTO CONTABLE",                "DEPTO. CONTABLE FINA","Analista Contable"),
    ("Diana Marcela Piedrahita Palacio",    "3727210979", "00.317.032", "PROMOTORA","COMERCIAL ARMENIA",                    "DEPTO COMERCIAL ARME","Representante de ventas"),
    ("Luz Deney Giraldo Cabrera",           "2051454923", "00.317.033", "PROMOTORA","COMERCIAL ARMENIA",                    "DEPTO COMERCIAL ARME","Representante de ventas"),
    ("Mateo Franco Vinasco",                "7280359794", "00.316.912", "PROMOTORA","COMERCIAL PEREIRA",                    "DEPTO COMERCIAL PERE","Coordinador Comercial"),
    ("Evelyn Gomez Agudelo",                "46231783",   "00.316.948", "PROMOTORA","COMERCIAL PEREIRA",                    "DEPTO COMERCIAL PERE","Representante de ventas"),
    ("Paola Andrea Orozco López",           "3392080953", "",           "PROMOTORA","COMERCIAL MANIZALES",                  "ADMON OFICINA PPAL", "Representante de ventas"),
    ("Yaritza Lilley Villamizar Uribe",     "8235363119", "",           "PROMOTORA","COMERCIAL MANIZALES",                  "ADMON OFICINA PPAL", "Representante de Ventas"),
    ("Mini Johana Rivera Gonzalez",         "4332894265", "00.316.937", "PROMOTORA","DIRECCIÓN DE OBRAS",                   "ADMON OFICINA PPAL", "Asistente de Obra"),
    ("Olga Lucia Gomez Barrios",            "40742311",   "",           "PROMOTORA","TALENTO HUMANO",                       "ADMON OFICINA PPAL", "Analista de Talento Humano"),
    ("Diego Alexander Marin Marin",         "4529615275", "",           "PROMOTORA","TALENTO HUMANO",                       "ADMON OFICINA PPAL", "Mensajero"),
    ("José Antonio Borja Sanchez",          "52339391",   "",           "PROMOTORA","TALENTO HUMANO",                       "ADMON OFICINA PPAL", "Administrador de Finca"),
    ("Fabio Fernandez Suarez",              "7730428",    "00.317.112", "PROMOTORA","POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  "Ayudante de Obra"),
    ("Yeison Fabian Morales Sabogal",       "5491946",    "00.317.111", "PROMOTORA","POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  ""),
    ("Maikol Javier Jiménez Henao",         "1284277889", "00.317.113", "PROMOTORA","POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  ""),
    ("Luis Antonio Gonzalez Valbuena",      "86125617",   "00.317.116", "PROMOTORA","POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  ""),
    ("Jairo Antonio Mesa Gonzalez",         "6279418",    "00.317.118", "PROMOTORA","POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  ""),
    ("Martha Elena Aristizabal Garcia",     "38538251",   "00.317.031", "PROMOTORA","OBRA MILAN 170 / CONSTRUCTIVO",        "MILAN 170",          "Coordinador de Obra"),
    ("Natalia Patiño Cardenas",             "8110054933", "00.317.029", "PROMOTORA","OBRA MILAN 170 / CONSTRUCTIVO",        "MILAN 170",          "Auxiliar en Seguridad y Salud en el Trabajo"),
    ("Sebastián Narváez Tamayo",            "2970753705", "00.317.030", "PROMOTORA","OBRA MILAN 170 / CONSTRUCTIVO",        "MILAN 170",          ""),
    ("Abelardo Rodas Bustamante",           "45551614",   "00.317.028", "PROMOTORA","OBRA MILAN 170 / CONSTRUCTIVO",        "MILAN 170",          ""),
    ("Andrey Molina Conde",                 "3342608",    "00.316.965", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       "Coordinador de Obra"),
    ("Willmar Alexander Villa Restrepo",    "7805745017", "00.316.966", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       "Oficial de Obra"),
    ("Cesar Augusto Cortes Gil",            "88320463",   "00.316.963", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       "Ayudante Practico de Obra"),
    ("Hernan Aranzalez",                    "63606628",   "00.316.967", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       "Maestro de Obra"),
    ("Cristian Gilberto Guevara Reyes",     "2554762903", "00.316.964", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       ""),
    ("Ricardo Antonio Orozco Hernández",    "28566572",   "00.316.969", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       "Coordinador SG-SST"),
    ("Jose Alvaro Burbano Velasquez",       "7483366056", "00.316.970", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       ""),
    ("Diosenel Gonzalez Perez",             "22201654",   "00.316.968", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       ""),
    ("José Ignacio Vallejo Diaz",           "4246059658", "00.316.972", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       ""),
    ("Diana Patricia Restrepo Román",       "4698408854", "00.316.971", "PROMOTORA","OBRA PRADERA VIVA / CONSTRUCTIVO",     "PRADERA-VIVA",       ""),
    ("Lina Andrea Aguilar Nuñez",           "30514014",   "",           "PROMOTORA","DIRECCIÓN DE OBRAS",                   "ADMON OFICINA PPAL", "Profesional de Gestión Logística"),
    ("Daniela Otalvaro Franco",             "3694860228", "",           "PROMOTORA","COMERCIAL PEREIRA",                    "DEPTO COMERCIAL PERE","Representante de ventas"),

    # ── YULDANA ──
    ("Clara Luz Giraldo Jaramillo",         "66661351",   "00.316.975", "YULDANA",  "INNOVACIÓN Y NUEVOS PROYECTOS",        "ADMON OFICINA PPAL", ""),
    ("Dyoney de Jesus Grajales Florez",     "90048665",   "00.317.154", "YULDANA",  "CENTRO COMERCIAL YULDANA / TALENTO HUMANO", "ADMON OFICINA PPAL", ""),

    # ── CALICANTO ──
    ("José Alejandro Mejia Giraldo",        "2719583",    "00.316.978", "CALICANTO","DESARROLLO DE NEGOCIOS",               "ADMON OFICINA PPAL", "Director Desarrollo de Negocios"),
    ("Laura Alejandra Duque Toro",          "5567816720", "",           "CALICANTO","DEPARTAMENTO CONTABLE",                "ADMON OFICINA PPAL", "Contador"),
    ("Camila Gonzalez Martinez",            "9573276057", "",           "CALICANTO","COMERCIAL ARMENIA",                    "ADMON OFICINA PPAL", "Representante de ventas"),
    ("Laura Nicole Osorio Valencia",        "7567496105", "",           "CALICANTO","COMERCIAL ARMENIA",                    "ADMON OFICINA PPAL", "Representante de Ventas Online"),
    ("Luis Enrique Torres Castellanos",     "9639245200", "",           "CALICANTO","ACOMPAÑAMIENTO AL CLIENTE",            "ADMON OFICINA PPAL", "Analista de Cartera"),
    ("Juan Camilo Rios Villegas",           "4095476665", "",           "CALICANTO","ACOMPAÑAMIENTO AL CLIENTE",            "ADMON OFICINA PPAL", "Coordinador de Acompañamiento al Cliente"),
    ("Sindy Carolina Soto Martínez",        "8047877267", "",           "CALICANTO","ACOMPAÑAMIENTO AL CLIENTE",            "ADMON OFICINA PPAL", "Asistente Administrativo"),
    ("Carolina Osorio Rodriguez",           "24972279",   "",           "CALICANTO","ACOMPAÑAMIENTO AL CLIENTE",            "ADMON OFICINA PPAL", "Asistente de Cartera"),
    ("Jhon Fredy Barbosa Leon",             "5924115",    "",           "CALICANTO","OBRA CAVANNA / CONSTRUCTIVO",          "CAVANNA",            "Maestro de Obra"),
    ("Darwin Alejandro Castrillon Ramirez", "2867302554", "",           "CALICANTO","OBRA CAVANNA / CONSTRUCTIVO",          "CAVANNA",            "Almacenista de Obra"),
    ("Gilberto Giraldo Gomez",              "8612220",    "",           "CALICANTO","POSTVENTA - ARMENIA",                  "POSTVENTA ARMENIA",  "Ayudante de Obra"),
    ("Juan Esteban Muñoz Bermudez",         "8385972235", "",           "CALICANTO","OBRA TERRUM / CONSTRUCTIVO",           "TERRUM",             "Almacenista de Obra"),
    ("Ever Antonio Ortega",                 "77187530",   "",           "CALICANTO","OBRA TERRUM / CONSTRUCTIVO",           "TERRUM",             "Ayudante de Obra"),
    ("Cristina Elizabeth Cerón Calvache",   "33978249",   "",           "CALICANTO","OBRA TERRUM / CONSTRUCTIVO",           "TERRUM",             "Coordinador de Obra"),
    ("Gustavo Adolfo Moreno Agudelo",       "78139880",   "",           "CALICANTO","COMERCIAL ARMENIA",                    "ADMON OFICINA PPAL", "Representante de Ventas"),
    ("Maria Juliana Rico Ospina",           "4919706735", "",           "CALICANTO","GESTIÓN TÉCNICA",                      "ADMON OFICINA PPAL", "Profesional de Proyectos"),
    ("Juan Sebastian Palacio Zuluaga",      "3615507143", "",           "CALICANTO","GESTIÓN TÉCNICA",                      "ADMON OFICINA PPAL", "Profesional de Diseño"),

    # ── QUIMBAYA ──
    ("Clarena Mejia Giraldo",               "9697354961", "",           "QUIMBAYA", "GERENCIA",                             "ADMON OFICINA PPAL", "Gerente"),
    ("Cristian Felipe Guevara Aguirre",     "5951406973", "",           "QUIMBAYA", "GERENCIA",                             "ADMON OFICINA PPAL", "Coordinador Gestion de Diseño"),

    # ── SERVICOL ──
    ("Diana Alejandra Martinez Guerrero",   "4274958945", "",           "SERVICOL", "MERCADEO",                             "ADMON OFICINA PPAL", "Lider Comunicaciones Digitales"),
    ("Lina Marcela Jaramillo Gómez",        "9592390865", "",           "SERVICOL", "DEPARTAMENTO CONTABLE",               "ADMON OFICINA PPAL", "Analista de impuestos"),
    ("Stephany Valencia Guevara",           "6687206971", "",           "SERVICOL", "GESTIÓN TÉCNICA",                      "ADMON OFICINA PPAL", "Asistente de Gestión Logistica"),
    ("Carolina Maria Florez Rincón",        "1083651970", "",           "SERVICOL", "ACOMPAÑAMIENTO AL CLIENTE",            "ADMON OFICINA PPAL", "Asistente Entrega de Inmuebles"),
    ("Juliana Cecilia Guzmán Castillo",     "9285415473", "",           "SERVICOL", "POSTVENTA - ARMENIA",                  "TERRUM",             "Secretaria de Obra"),
    ("Victor Manuel Rubio Salazar",         "2320763135", "",           "SERVICOL", "OBRA CAVANNA / CONSTRUCTIVO",          "CAVANNA",            "Ayudante de Obra"),
]


def seed():
    db: Session = SessionLocal()
    try:
        if db.query(User).first():
            print("⚠️  Base de datos ya tiene datos. Saltando seed.")
            return

        print("🌱 Iniciando seed...")

        # ── Companies ──
        company_map = {}
        for c in COMPANIES:
            co = Company(**c)
            db.add(co)
            db.flush()
            company_map[c["short_name"]] = co
        print(f"  ✔ {len(COMPANIES)} empresas creadas")

        # ── Departments ──
        dept_map = {}  # (company_short, dept_name) -> Department
        for co_short, dept_names in DEPARTMENTS.items():
            co = company_map[co_short]
            for name in dept_names:
                dept = Department(name=name, company_id=co.id)
                db.add(dept)
                db.flush()
                dept_map[(co_short, name)] = dept
        total_depts = sum(len(v) for v in DEPARTMENTS.values())
        print(f"  ✔ {total_depts} departamentos creados")

        # ── Employees ──
        emp_count = 0
        for (full_name, cedula, internal_code, co_short, dept_name, project_code, cargo) in EMPLOYEES:
            co = company_map.get(co_short)
            if not co:
                continue
            dept = dept_map.get((co_short, dept_name))
            if not dept:
                # create department on the fly if not in predefined list
                dept = Department(name=dept_name, company_id=co.id)
                db.add(dept)
                db.flush()
                dept_map[(co_short, dept_name)] = dept

            emp = Employee(
                full_name=full_name,
                cedula=cedula,
                internal_code=internal_code or None,
                department_id=dept.id,
                company_id=co.id,
                project_code=project_code or None,
                cargo=cargo or None,
            )
            db.add(emp)
            emp_count += 1
        print(f"  ✔ {emp_count} empleados creados")

        # ── Pay period (current) ──
        now = datetime.now()
        month_names = {
            1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
            7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
        }
        p1 = PayPeriod(
            year=now.year, month=now.month,
            month_name=month_names[now.month],
            period_number=1, period_label="Primera Quincena",
        )
        p2 = PayPeriod(
            year=now.year, month=now.month,
            month_name=month_names[now.month],
            period_number=2, period_label="Segunda Quincena",
        )
        db.add(p1)
        db.add(p2)
        db.flush()
        print(f"  ✔ 2 períodos creados ({month_names[now.month]} {now.year})")

        # ── Default users ──
        admin_user = User(
            username="admin",
            full_name="Administrador",
            password_hash=hash_password("admin123"),
            role=UserRole.admin,
        )
        hr_user = User(
            username="talento",
            full_name="Talento Humano Personal",
            password_hash=hash_password("talento123"),
            role=UserRole.hr,
        )
        db.add(admin_user)
        db.add(hr_user)
        db.flush()

        # One manager per company
        manager_users = []
        for co_short in ["CAMU", "ALICANTE", "PROMOTORA", "YULDANA", "CALICANTO"]:
            u = User(
                username=f"jefe_{co_short.lower()}",
                full_name=f"Jefe {co_short}",
                password_hash=hash_password("jefe123"),
                role=UserRole.manager,
            )
            db.add(u)
            db.flush()
            manager_users.append((u, co_short))

        # Assign all departments of each company to the matching manager
        for u, co_short in manager_users:
            for (cs, _), dept in dept_map.items():
                if cs == co_short:
                    db.add(ManagerDepartment(user_id=u.id, department_id=dept.id))

        db.commit()
        print(f"  ✔ {2 + len(manager_users)} usuarios creados")
        print()
        print("✅ Seed completado. Credenciales por defecto:")
        print("   admin    / admin123   (Administrador)")
        print("   talento  / talento123 (Talento Humano)")
        print("   jefe_camu / jefe123   (Jefe CAMU)")
        print("   jefe_alicante / jefe123")
        print("   jefe_promotora / jefe123")
        print("   jefe_yuldana / jefe123")
        print("   jefe_calicanto / jefe123")

    except Exception as e:
        db.rollback()
        print(f"❌ Error en seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
