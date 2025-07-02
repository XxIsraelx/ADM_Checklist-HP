import datetime
import flet as ft
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
from flet import WEB_BROWSER
from datetime import datetime, date
import os
import json


COR_AZUL_CLARO = ft.Colors.BLUE_100
COR_CINZA_CLARO = ft.Colors.GREY_200

def extrair_inteiro(valor):
    if not valor or str(valor).strip() in ["", "0"]:
        return 1
    valor_str = str(valor)
    numeros = re.findall(r"\d+", valor_str.replace(".", "").replace(",", ""))
    return int("".join(numeros)) if numeros else 1

def cor_gradiente(proporcao):
    verde = (76, 175, 80)
    vermelho = (244, 67, 54)
    r = int(verde[0] + (vermelho[0] - verde[0]) * proporcao)
    g = int(verde[1] + (vermelho[1] - verde[1]) * proporcao)
    b = int(verde[2] + (vermelho[2] - verde[2]) * proporcao)
    return f"#{r:02x}{g:02x}{b:02x}"

def obter_credenciais():
    escopo = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_str = os.environ.get("GOOGLE_CREDS_JSON")
    if not json_str:
        raise Exception("Variável de ambiente GOOGLE_CREDENTIALS_JSON não definida.")
    dados = json.loads(json_str)
    return ServiceAccountCredentials.from_json_keyfile_dict(dados, escopo)

def ler_checklists():
    credenciais = obter_credenciais()
    cliente = gspread.authorize(credenciais)
    planilha = cliente.open("DADOS CHECKLIST_FLET")
    aba = planilha.worksheet("Checklist")
    return aba.get_all_records()

def main(page: ft.Page):
    pagina_atual = "relatorios"
    page.title = "Painel de Checklists"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    drawer_visivel = True  # controle da visibilidade da barra lateral

    is_mobile = page.platform in ["android", "ios"]

    PLACAS_CADASTRADAS = [
        "GHV2E21", "GAF8H52", "FCP3833", "FPA0048", "GIP2645", "GIO1270",
        "FZG1079", "FYP6D17", "CUK7J38", "FAV7246", "FJQ9004", "FIW1F28",
        "FQL9C47", "BYQ0D86", "FXG9543", "FIO8847", "GHG6179", "FTE8G63",
        "FPD6062", "EZY2H13", "GAP9701", "FGW3125", "FYW9H71", "FCN3J16",
        "FIQ5337", "FYK9E28"
    ]  # placas fixas

    # Definição dos filtros e controles usados na página "Não Enviados"
    filtro_placa = ft.Dropdown(
        width=160,
        label="Placa",
        options=[ft.dropdown.Option("Todas as Placas")] + [ft.dropdown.Option(p) for p in PLACAS_CADASTRADAS],
        value="Todas as Placas",
        icon=ft.Icons.DIRECTIONS_CAR,
        on_change=lambda e: atualizar_ocorrencias(),
    )



    filtro_data_text = ft.Text(value="", width=130, text_align=ft.TextAlign.CENTER)
    

    def on_date_change(e):
        data = e.control.value
        filtro_data_text.value = data.strftime("%Y-%m-%d") if data else ""
        atualizar_ocorrencias()
        page.update()

    date_picker = ft.DatePicker(
        on_change=on_date_change,
        first_date= date(2024, 1, 1),
        last_date= date(2030, 12, 31),
    )

    def abrir_date_picker():
        page.dialog = date_picker
        date_picker.open = True
        page.update()

    filtro_data_btn = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH,
        tooltip="Selecionar data",
        on_click=lambda e: abrir_date_picker(),  # ✅ chama a função correta
    )

    filtro_data = ft.Row(
        controls=[filtro_data_text, filtro_data_btn],
        spacing=5,
    )

    page.overlay.append(date_picker)

    filtro_data = ft.Row(
        controls=[filtro_data_text, filtro_data_btn],
        spacing=5,
    )



    # Painéis usados para cada página
    painel = ft.Column(scroll=ft.ScrollMode.ALWAYS)
    detalhes = ft.Column(scroll=ft.ScrollMode.ALWAYS)

    painel_ocorrencias = ft.Column(
        [
            ft.Text("Página de Ocorrências Não Enviadas", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Aqui vamos desenvolver o monitoramento das ocorrências que não foram enviadas."),
        ],
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
    )

    content_area = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.ALWAYS,
        alignment=ft.MainAxisAlignment.START
    )

    # Filtros para a página "Relatórios"
    filtro_motorista = ft.Dropdown(
        width=160,
        hint_text="Selecione o motorista",
        label=None if is_mobile else "Motorista",
        options=[],
        autofocus=False,
        icon=ft.Icons.PERSON,
        on_change=lambda e: carregar_painel(),
    )

    filtro_data_dropdown = ft.Dropdown(
        width=165,
        hint_text="Selecione a data",
        label=None if is_mobile else "Data",
        options=[],
        icon=ft.Icons.CALENDAR_MONTH,
        on_change=lambda e: carregar_painel(),
    )

    def carregar_painel(e=None):
        try:
            registros = ler_checklists()
        except Exception as err:
            painel.controls = [ft.Text(f"Erro ao carregar dados: {err}", color=ft.Colors.RED)]
            content_area.controls.clear()
            content_area.controls.append(painel)
            page.update()
            return

        if not registros:
            painel.controls = [ft.Text("Nenhum checklist encontrado.")]
            content_area.controls.clear()
            content_area.controls.append(painel)
            page.update()
            return

        # Salva os valores atuais dos filtros
        motorista_selecionado = filtro_motorista.value
        data_selecionada = filtro_data_dropdown.value

        # Atualiza as opções dos filtros (mantendo o valor selecionado)
        motoristas = sorted(set(r["Motorista"] for r in registros if r["Motorista"]))
        filtro_motorista.options.clear()
        filtro_motorista.options.append(ft.dropdown.Option("Todos os Motoristas"))  # ✅ adiciona opção "Todos"
        filtro_motorista.options.extend([ft.dropdown.Option(m) for m in motoristas])

        datas_unicas = sorted(
            {r["Carimbo Data/Hora"].split()[0] for r in registros if r["Carimbo Data/Hora"]},
            reverse=True
        )
        filtro_data_dropdown.options.clear()
        filtro_data_dropdown.options.append(ft.dropdown.Option("Todas as Datas"))
        filtro_data_dropdown.options.extend([ft.dropdown.Option(d) for d in datas_unicas])

        # Aplica os filtros
        registros_filtrados = registros
        if filtro_motorista.value and filtro_motorista.value != "Todos os Motoristas":
            registros_filtrados = [r for r in registros_filtrados if r["Motorista"] == filtro_motorista.value]

        if filtro_data_dropdown.value and filtro_data_dropdown.value != "Todas as Datas":
            registros_filtrados = [r for r in registros_filtrados if r["Carimbo Data/Hora"].startswith(filtro_data_dropdown.value)]


        # Cria os cards
        cards = []
        for r in registros_filtrados:
            solucionada = r.get("Solucionada", "").lower() in ["sim", "true", "1"]
            icon = ft.Icons.CHECK_CIRCLE if solucionada else ft.Icons.ERROR
            color = ft.Colors.GREEN if solucionada else ft.Colors.ORANGE

            cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(name=icon, color=color, size=24),
                                        ft.Text(f"Placa: {r.get('Placa', '')}", size=18, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Text(f"Data: {r.get('Carimbo Data/Hora', '')}", size=12, color=ft.Colors.BLACK54),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Row(
                                    [
                                        ft.Text(f"Motorista: {r.get('Motorista', '')}", size=14, color=ft.Colors.BLACK54),
                                        ft.TextButton("Ver detalhes", on_click=lambda e, r=r: ir_para_detalhes(r)),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                            ]
                        ),
                        padding=15,
                        width=320,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        shadow=ft.BoxShadow(color="#1A000000", blur_radius=8, offset=ft.Offset(2, 2)),
                    ),
                    elevation=5,
                    margin=ft.margin.only(left=50, top=8, bottom=8, right=8),
                )
            )

        painel.controls = [
            ft.ResponsiveRow(
                controls=[ft.Column(col={"xs": 12, "sm": 6, "md": 4, "lg": 3}, controls=[card]) for card in cards],
                spacing=10,
                run_spacing=10,
                alignment=ft.MainAxisAlignment.START,
            )
        ]

        content_area.controls.clear()
        content_area.controls.append(
            ft.Column(
                [
                    ft.Text("Painel de Checklists", size=26, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row(
                        controls=[
                            ft.Row([ft.Icon(ft.Icons.PERSON), filtro_motorista], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH), filtro_data_dropdown], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    painel,
                ],
                alignment=ft.MainAxisAlignment.START,
                expand=True,
            )
        )
        page.update()


    def ir_para_detalhes(registro):
        detalhes.controls.clear()

        comentario_input = ft.TextField(
            label="Comentários", multiline=True, value=registro.get("Comentários", ""), visible=False
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Em análise"),
                ft.dropdown.Option("Solucionada"),
            ],
            value="Solucionada" if registro.get("Solucionada", "").lower() in ["sim", "true", "1"] else "Em análise",
            visible=False,
        )
        salvar_btn = ft.ElevatedButton("Salvar Alteração", visible=False)

        def ativar_edicao(e):
            comentario_input.visible = True
            status_dropdown.visible = True
            salvar_btn.visible = True
            page.update()

        status_atual = registro.get("Solucionada", "").lower() in ["sim", "true", "1"]
        icone_status = ft.Icons.CHECK_CIRCLE if status_atual else ft.Icons.HOURGLASS_TOP
        cor_status = ft.Colors.GREEN if status_atual else ft.Colors.AMBER

        cabecalho = ft.Container(
            bgcolor=COR_CINZA_CLARO,
            padding=15,
            border_radius=10,
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Row([ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE),
                                    ft.Text(f"Motorista: {registro.get('Motorista', '')}", size=18, weight=ft.FontWeight.BOLD)]),
                            ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.BLUE),
                                    ft.Text(f"Data: {registro.get('Carimbo Data/Hora', '').split()[0]}", size=16)]),
                            ft.Row([ft.Icon(ft.Icons.DIRECTIONS_CAR, color=ft.Colors.BLUE),
                                    ft.Text(f"Placa: {registro.get('Placa', '')}", size=16)]),
                        ],
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Icon(icone_status, color=cor_status, size=28),
                            ft.IconButton(
                                icon=ft.Icons.EDIT_NOTE,
                                tooltip="Editar Ocorrência",
                                icon_color=ft.Colors.GREEN,
                                style=ft.ButtonStyle(bgcolor="#1A4CAF50"),
                                on_click=ativar_edicao,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=27,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        detalhes.controls.append(cabecalho)

        def criar_bloco(titulo, icone, conteudos):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(icone, color=ft.Colors.BLUE), ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD)]),
                        ft.Divider(),
                        *conteudos,
                    ]
                ),
                bgcolor=COR_CINZA_CLARO,
                border_radius=10,
                padding=10,
                margin=ft.margin.only(top=10),
            )

        bloco_veiculo = []
        bloco_checklist = []
        bloco_outros = []

        for campo, valor in registro.items():
            campo_lower = campo.lower()
            if campo_lower in ["motorista", "placa", "carimbo data/hora"]:
                bloco_veiculo.append(ft.Row([ft.Text(f"{campo}:", width=180), ft.Text(str(valor))]))
            elif "freio" in campo_lower:
                bloco_checklist.append(ft.Row([ft.Text(f"{campo}:", width=180), ft.Text(str(valor))]))
            elif campo_lower in ["observação", "observacao"]:
                bloco_outros.append(ft.Row([ft.Text(f"{campo}:", width=180), ft.Text(str(valor))]))
            elif campo_lower not in ["solucionada", "km atual", "km troca de oleo", "nível do óleo", "observação", "observacao", "carimbo data/hora"]:
                bloco_checklist.append(ft.Row([ft.Text(f"{campo}:", width=180), ft.Text(str(valor))]))

        detalhes.controls.extend(
            [
                criar_bloco("Informações do Veículo", ft.Icons.DIRECTIONS_CAR, bloco_veiculo),
                criar_bloco("Itens do Checklist", ft.Icons.CHECKLIST, bloco_checklist),
                criar_bloco("Outros Dados", ft.Icons.DESCRIPTION, bloco_outros),
            ]
        )

        try:
            km_atual = extrair_inteiro(registro.get("Km atual", "0"))
            km_troca = extrair_inteiro(registro.get("Km troca de oleo", "1"))
            proporcao = min(max(km_atual / (km_troca if km_troca else 1), 0), 1)
            cor_barra = cor_gradiente(proporcao)

            detalhes.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(name=ft.Icons.OIL_BARREL, color=ft.Colors.BLUE),
                                    ft.Text("Nível do Óleo (KM Atual vs KM da Troca)", weight=ft.FontWeight.BOLD),
                                ],
                                spacing=10,
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            ft.ProgressBar(value=proporcao, color=cor_barra),
                            ft.Row(
                                [
                                    ft.Text(f"KM Atual: {km_atual}"),
                                    ft.Text(f"KM da Troca: {km_troca}"),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ]
                    ),
                    bgcolor=COR_CINZA_CLARO,
                    padding=10,
                    border_radius=10,
                    margin=ft.margin.only(top=10),
                )
            )

        except Exception as err:
            detalhes.controls.append(ft.Text(f"Erro ao calcular nível do óleo: {err}", color=ft.Colors.RED))

        detalhes.controls.append(comentario_input)
        detalhes.controls.append(status_dropdown)
        detalhes.controls.append(salvar_btn)

        def salvar_alteracao(e):
            try:
                registros = ler_checklists()
                cliente = gspread.authorize(obter_credenciais())
                planilha = cliente.open("DADOS CHECKLIST_FLET")
                aba = planilha.worksheet("Checklist")

                for i, r in enumerate(registros, start=2):
                    if r["Carimbo Data/Hora"] == registro["Carimbo Data/Hora"]:
                        aba.update_cell(i, list(r.keys()).index("Solucionada") + 1, "Sim" if status_dropdown.value == "Solucionada" else "Não")
                        if "Comentários" in r:
                            aba.update_cell(i, list(r.keys()).index("Comentários") + 1, comentario_input.value)

                        detalhes.controls.append(ft.Text("Alteração salva com sucesso!", color=ft.Colors.GREEN))
                        carregar_painel()
                        page.update()
                        return

                detalhes.controls.append(ft.Text("Registro não encontrado.", color=ft.Colors.RED))
                page.update()

            except Exception as err:
                detalhes.controls.append(ft.Text(f"Erro ao salvar: {err}", color=ft.Colors.RED))
                page.update()

        salvar_btn.on_click = salvar_alteracao

        content_area.controls.clear()
        content_area.controls.append(detalhes)
        nonlocal pagina_atual
        pagina_atual = "detalhes"
        page.update()

    def atualizar_ocorrencias(e=None):
        try:
            registros = ler_checklists()
        except Exception as err:
            painel_ocorrencias.controls = [ft.Text(f"Erro ao carregar dados: {err}", color=ft.Colors.RED)]
            page.update()
            return

        data_selecionada = filtro_data_text.value
        placa_selecionada = filtro_placa.value

        cards = []

        # Converte a data selecionada para datetime.date para comparar
        try:
            data_selecionada_dt = datetime.strptime(data_selecionada, "%Y-%m-%d").date()
        except Exception:
            data_selecionada_dt = None

        for placa in PLACAS_CADASTRADAS:
            if placa_selecionada and placa_selecionada != "Todas as Placas" and placa != placa_selecionada:
                continue

            encontrado = None

            for r in registros:
                carimbo = r.get("Carimbo Data/Hora", "")
                placa_r = r.get("Placa", "")

                data_hora_dt = None
                try:
                    data_hora_dt = datetime.strptime(carimbo, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    try:
                        data_hora_dt = datetime.strptime(carimbo, "%d/%m/%Y %H:%M")
                    except ValueError:
                        print(f"Erro ao converter data da planilha: {carimbo}")

                data_r = data_hora_dt.date() if data_hora_dt else None

                if placa_r == placa and data_r == data_selecionada_dt:
                    encontrado = r
                    break

            if encontrado:
                status = "Enviado"
                motorista = encontrado.get("Motorista", "Desconhecido")
                icone = ft.Icons.CHECK_CIRCLE
                cor = ft.Colors.GREEN
                tooltip_text = "Checklist enviado"
            else:
                status = "Checklist Pendente"
                motorista = "Pendente"
                icone = ft.Icons.ERROR_OUTLINE
                cor = ft.Colors.RED
                tooltip_text = "Checklist ainda não enviado"

            cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(icone, color=cor, tooltip=tooltip_text),
                                ft.Text(f"Placa: {placa}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"Status: {status}", color=cor),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text(f"Motorista: {motorista}"),
                                ft.Text(f"Data: {data_selecionada}"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ]),
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        shadow=ft.BoxShadow(color="#1A000000", blur_radius=8, offset=ft.Offset(2, 2)),
                    ),
                    margin=ft.margin.all(8),
                )
            )

        painel_ocorrencias.controls.clear()
        painel_ocorrencias.controls.append(
            ft.Column(
                [
                    ft.Text("Ocorrências por Veículo", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([filtro_placa, filtro_data], spacing=10),
                    *cards
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )
        page.update()



    # Navegação entre páginas
    def mostrar_pagina(nome):
        nonlocal pagina_atual
        pagina_atual = nome
        if nome == "relatorios":
            carregar_painel()
        elif nome == "ocorrencias":
            atualizar_ocorrencias()
            content_area.controls.clear()
            content_area.controls.append(painel_ocorrencias)  # <-- adicionar o painel na tela
        page.update()


    def voltar_ou_trocar(e):
        nonlocal pagina_atual
        if pagina_atual == "detalhes":
            mostrar_pagina("relatorios")
        else:
            novo_index = 1 if drawer.selected_index == 0 else 0
            drawer.selected_index = novo_index
            mostrar_pagina(["relatorios", "ocorrencias"][novo_index])
        page.update()

    # Barra lateral (drawer)
    def ao_trocar_menu(e):
        idx = e.control.selected_index
        if idx == 0:
            mostrar_pagina("relatorios")
        elif idx == 1:
            mostrar_pagina("ocorrencias")
        elif idx == 2:
            if pagina_atual == "detalhes":
                mostrar_pagina("relatorios")
            else:
                drawer.selected_index = 0
                mostrar_pagina("relatorios")
        page.update()

    drawer = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD, label="Relatórios"),
            ft.NavigationRailDestination(icon=ft.Icons.ERROR, label="Não Enviados"),
            ft.NavigationRailDestination(icon=ft.Icons.ARROW_BACK, label="Voltar"),
        ],
        on_change=ao_trocar_menu,
        extended=True,
        min_width=30,
        min_extended_width=150,
    )

    divider = ft.VerticalDivider(width=1)

    main_row = ft.Row(
        [
            drawer,
            divider,
            content_area,
        ],
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    def toggle_drawer(e):
        nonlocal drawer_visivel
        drawer_visivel = not drawer_visivel
        if drawer_visivel:
            if drawer not in main_row.controls:
                main_row.controls.insert(0, drawer)
            if divider not in main_row.controls:
                main_row.controls.insert(1, divider)
            content_area.expand = True
        else:
            if drawer in main_row.controls:
                main_row.controls.remove(drawer)
            if divider in main_row.controls:
                main_row.controls.remove(divider)
            content_area.expand = True
        page.update()

    toggle_button = ft.IconButton(
        icon=ft.Icons.MENU,
        tooltip="Mostrar/Ocultar barra lateral",
        on_click=toggle_drawer,
        icon_size=30,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        bgcolor=ft.Colors.BLUE_200,
        icon_color=ft.Colors.WHITE,
        width=50,
        height=50,
    )

    toggle_container = ft.Container(
        content=toggle_button,
        alignment=ft.alignment.center_left,
        padding=ft.padding.only(left=5),
        width=60,
        height=page.height,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    page.overlay.append(toggle_container)

    def on_resize(e):
        mobile = page.window_width < 600
        filtro_motorista.label = None if mobile else "Motorista"
        filtro_data_dropdown.label = None if mobile else "Data"
        page.update()



    page.on_resize = on_resize

    page.add(main_row)

    mostrar_pagina("relatorios")

ft.app(target=main, view=WEB_BROWSER)
