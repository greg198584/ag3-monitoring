import requests
import time
from rich.console import Console
from rich.table import Table
from rich import box
import schedule
import argparse
from functools import partial
from rich.columns import Columns
from rich.progress import Progress
import json

watchOnly = False
def generate_programme_table(data):
    # Tableau pour afficher les informations du programme
    programme_table = Table(show_header=True, header_style="bold magenta")
    programme_table.box = box.SIMPLE_HEAVY
    programme_table.add_column("Programme")

    programme_table.add_row("ID", data["id"])
    programme_table.add_row("Nom", data["name"])
    programme_table.add_row("Secteur ID", str(data["position"]["secteur_id"]))
    programme_table.add_row("Zone ID", str(data["position"]["zone_id"]))
    programme_table.add_row("Dernière position", f'Secteur ID: {data["last_position"]["secteur_id"]}, Zone ID: {data["last_position"]["zone_id"]}')
    programme_table.add_row("Niveau", str(data["level"]))
    programme_table.add_row("Statut", "[green]YES[/green]") if data["status"] else "[red]NO[/red]"
    programme_table.add_row("Exploration", "[green]YES[/green]" if data["exploration"] else "[red]NO[/red]")

    flagCapture = False
    for cellule in data["cellules"].values():
        for dataCellule in cellule["datas"].values():
            if dataCellule["is_flag"]:
                flagCapture = True

    programme_table.add_row("Flag-found", "[green]YES[/green]" if flagCapture else "[red]NO[/red]")
    return programme_table

def generate_cellules_table(data):
    # Tableau pour afficher les informations des cellules
    cellules_table = Table(show_header=True, header_style="bold magenta")
    cellules_table.box = box.SIMPLE_HEAVY
    cellules_table.add_column("Cellule ID", justify="center")
    cellules_table.add_column("Valeur", justify="center")
    cellules_table.add_column("Énergie", justify="center")
    cellules_table.add_column("Statut", justify="center")
    cellules_table.add_column("Capture", justify="center")
    cellules_table.add_column("Piégé", justify="center")
    cellules_table.add_column("Exploration", justify="center")

    for cellule in data["cellules"].values():
        cellules_table.add_row(
            str(cellule["id"]),
            "[cyan]" + str(cellule["valeur"]) + "[/cyan]",
            "[yellow]" + str(cellule["energy"]) + "[/yellow]",
            "[green]actif[/green]" if cellule["status"] else "[red]Inactif[/red]",
            "[red]captureable[/red]" if cellule["capture"] else "[green]captureable[/green]",
            "[green]trapped[/green]" if cellule["trapped"] else "[red]trapped[/red]",
            "[green]exploration[/green]" if cellule["exploration"] else "[red]exploration[/red]",
        )

    return cellules_table

def generate_navigation_table(data):
    # Tableau pour afficher les informations de navigation
    navigation_table = Table(show_header=True, header_style="bold magenta")
    navigation_table.box = box.SIMPLE_HEAVY
    navigation_table.add_column("Navigation")

    navigation_table.add_row("Team", "[cyan]BLUE[/cyan]" if data["blue_team"] else "[red]RED[/red]")
    navigation_table.add_row("En cours", "[green]YES[/green]" if data["navigation"] else "[green]NO[/green]")
    navigation_table.add_row("Temps d'arrivée", data["navigation_time_arrived"])

    return navigation_table

def generate_tables(data):
    programme_table = generate_programme_table(data["programme"])
    cellules_table = generate_cellules_table(data["programme"])
    navigation_table = generate_navigation_table(data)

    return Columns([programme_table, cellules_table, navigation_table])

def generate_grid(zones):
    table = Table(show_header=True, header_style="bold magenta")
    table.box = box.SIMPLE_HEAVY
    taille = zones["taille"]
    grid_name = zones["ag-3-team"]
    zones = zones["zones"]

    table.add_column("grid: " + grid_name, justify="center")
    # Ajouter les colonnes pour chaque zone
    for zone_id in range(taille):
        table.add_column(str(zone_id), justify="center")

    # row_data = []
    # for i in range(taille):
    #     row_data.append("[cyan]" + str(i) + "[/cyan]")
    # table.add_row(*row_data)
    # Ajouter les lignes pour chaque secteur
    for secteur_id in range(taille):
        row_data = []
        row_data.append("[cyan]" + str(secteur_id) + "[/cyan]")
        for zone_id in range(taille):
            zone = next((z for z in zones if z["secteur_id"] == secteur_id and z["zone_id"] == zone_id), None)
            if zone is not None:
                if not zone["status"]:
                    row_data.append("[red].[/red]")
                elif zone["actif"]:
                    row_data.append("[green]X[/green]")
                else:
                    row_data.append("[blue]S[/blue]")
            else:
                row_data.append(" ")
        table.add_row(*row_data)
    return table

def generate_zone_data_table(program_data):
    table = Table(show_header=True, header_style="bold magenta")
    table.box = box.SIMPLE_HEAVY
    table.add_column("Zone Data", justify="center")
    if "id" not in program_data:
        return table
    table.add_row("ID", str(program_data["id"]))
    table.add_row("Actif", "[green]YES[/green]" if program_data["actif"] else "[red]NO[/red]")
    cellule_table = Table(show_header=True, header_style="bold magenta")
    cellule_table.box = box.SIMPLE_HEAVY
    cellule_table.add_column("Cellule ID")
    cellule_table.add_column("Valeur")
    cellule_table.add_column("Data")
    cellule_table.add_column("Status")
    cellule_table.add_column("Destroy")
    cellule_table.add_column("Rebuild")
    cellule_table.add_column("Capture")
    cellule_table.add_column("Trapped")
    for cellule in program_data["cellule"]:
        cellule_table.add_row(str(cellule["id"]),
                              str(cellule["valeur"]),
                              str(cellule["data_count"]),
                              "[green]YES[/green]" if cellule["status"] else "[red]NO[/red]",
                              "[green]YES[/green]" if cellule["destroy"] else "[red]NO[/red]",
                              "[green]YES[/green]" if cellule["rebuild"] else "[red]NO[/red]",
                              "[green]YES[/green]" if cellule["capture"] else "[red]NO[/red]",
                              "[green]YES[/green]" if cellule["trapped"] else "[red]NO[/red]")
    table.add_row("Cellules", cellule_table)
    return table

def display_program_data(program_data, table_title):
    # Créer une console Rich
    console = Console()

    # Créer une table pour afficher les données du programme
    table = Table(title=table_title)

    # Ajouter les colonnes à la table
    table.add_column("Cellules", justify="left", style="cyan")
    table.add_column("Statut", style="cyan")
    table.add_column("Nom", style="cyan")
    table.add_column("Level", style="cyan")

    # Récupérer les données des cellules pour le programme
    cell_data = program_data['cellules']

    max_valeur = program_data['level']*100
    # Afficher les données de chaque cellule
    for cell_id, cell_info in cell_data.items():
        # Créer une barre de progression pour le niveau de la cellule
        with Progress(transient=True) as progress:
            task_id = progress.add_task(f"Cellule {cell_id}", total=max_valeur)
            for i in range(cell_info['valeur']):
                progress.advance(task_id)
        # Déterminer la couleur de la barre en fonction du niveau de la cellule
        calcule = max_valeur / 2
        # print("max_valeur = ", int(max_valeur))
        # print("calcule_diviser = ", int(calcule))
        # print("valeur_cell = ", cell_info['valeur'])
        if cell_info['valeur'] <= int(max_valeur / 2):
            style = "red"
        elif cell_info['valeur'] >= int(max_valeur / 2):
            style = "yellow"
        else:
            style = "green"
        # Créer une colonne pour afficher la barre de progression
        progress_column = Columns([f"[{style}]Cellule {cell_id}[/{style}]", progress], expand=True)
        # Ajouter une ligne à la table pour la cellule
        status_str = "[red]Dommage[/red]" if cell_info['status'] == False else "[green]OK[/green]"
        table.add_row(progress_column, status_str, program_data['name'], str(program_data['level']))

    # Afficher la table dans la console Rich
    console.print(table)


def display_lock_program(json_data):
    # Récupérer les données des programmes
    prog_data = json_data['programme']
    lock_prog_data = json_data['lock_programme']

    # Afficher les données du programme principal
    table_title = f"[bold blue]{prog_data['name']}[/bold blue] (Level {prog_data['level']})"
    display_program_data(prog_data, table_title)

    # Afficher les données des programmes verrouillés
    for lock_prog_id, lock_prog_info in lock_prog_data.items():
        table_title = f"[bold green]{lock_prog_info['name']}[/bold green] (Level {lock_prog_info['level']})"
        display_program_data(lock_prog_info, table_title)

def generate_info_grid_table(data):
    # Tableau pour afficher les informations grille
    info_grid_table = Table(show_header=True, header_style="bold magenta")
    info_grid_table.box = box.SIMPLE_HEAVY
    info_grid_table.add_column("Grid infos")
    info_grid_table.add_row("Grille", data["ag-3-team"])
    info_grid_table.add_row("Cycle", str(data["cycle"]))
    info_grid_table.add_row("Iteration", str(data["iteration"]))
    info_grid_table.add_row("Progs", str(data["nbr_programmes"]))
    info_grid_table.add_row("Zone transfert", f'Secteur ID: {data["zone_transfert"]["secteur_id"]}, Zone ID: {data["zone_transfert"]["zone_id"]}')
    info_grid_table.add_row("Statut", "[green]YES[/green]") if data["status"] else "[red]NO[/red]"
    info_grid_table.add_row("Flag capture", "[green]YES[/green]" if data["flag_capture"] else "[red]NO[/red]")

    return info_grid_table
def refresh_grids(host_a, host_b, current_host, id, secret_id):
    console = Console(style="default")
    # Faire une requête HTTP pour obtenir l'objet JSON pour la première grille
    status_a_url = 'http://:host/v1/grid'
    status_a_url = status_a_url.replace(':host', host_a) if host_a else status_a_url
    response1 = requests.get(status_a_url)
    data1 = response1.json()

    # Générer la première grille
    g1 = generate_grid(data1)

    # Faire une requête HTTP pour obtenir l'objet JSON pour la deuxième grille
    status_b_url = 'http://:host/v1/grid'
    status_b_url = status_b_url.replace(':host', host_b) if host_b else status_b_url
    response2 = requests.get(status_b_url)
    data2 = response2.json()

    # Générer la deuxième grille
    g2 = generate_grid(data2)

    console.clear()  # Effacer l'écran

    # Générer données des grilles A et B
    info_grille_a = generate_info_grid_table(data1)
    info_grille_b = generate_info_grid_table(data2)

    # Afficher les deux grilles côte à côte + info
    console.print(Columns([g1, info_grille_a, g2, info_grille_b]))

    if watchOnly == False:
        # Scan zone
        scan_url = 'http://:host/v1/programme/scan/:id/:secret_id'
        scan_url = scan_url.replace(':host', current_host) if current_host else scan_url
        scan_url = scan_url.replace(':id', id) if id else scan_url
        scan_url = scan_url.replace(':secret_id', secret_id) if secret_id else scan_url
        response = requests.get(scan_url)
        program_data = response.json()

        # Générer la table des données du scan zone current
        zone_data = generate_zone_data_table(program_data)

        console.print(zone_data)

        # Faire une requête HTTP pour obtenir l'objet JSON
        prog_url = 'http://:host/v1/programme/infos/:id/:secret_id'
        prog_url = prog_url.replace(':host', current_host) if current_host else prog_url
        prog_url = prog_url.replace(':id', id) if id else prog_url
        prog_url = prog_url.replace(':secret_id', secret_id) if secret_id else prog_url

        response = requests.get(prog_url)
        programme_data = response.json()
        programme_tab = generate_tables(programme_data)
        console.print(programme_tab)
        display_lock_program(programme_data)

def refresh_grids_wrapper(host_a, host_b, current_host, id, secret_id):
    return partial(refresh_grids, host_a, host_b, current_host, id, secret_id)

def main(params):
    if "id" in params:
        print(f"L'ID du programme est {params['id']}")
    else:
        print("L'ID du programme n'a pas été renseigné")
        return

    if "secret-id" in params:
        print(f"Le Secret ID est {params['secret-id']}")
    else:
        print("Le Secret ID n'a pas été renseigné")
        return

    if "host_a" in params:
        print(f"host: {params['host_a']}")
    else:
        print("host a non renseigné")
        return

    if "host_b" in params:
        print(f"host: {params['host_b']}")
    else:
        print("host b non renseigné")
        return

    if "current_host" in params:
        print(f"current host: {params['current_host']}")
    else:
        print("current host non renseigné")
        return

    id = params["id"]
    secret_id = params["secret-id"]
    host_a = params["host_a"]
    host_b = params["host_b"]
    current_host = params["current_host"]
    refresh_grids_partial = refresh_grids_wrapper(host_a, host_b, current_host, id, secret_id)
    schedule.every(5).seconds.do(refresh_grids_partial)

    while True:
        schedule.run_pending()
        # Attendre 5 secondes avant de mettre à jour les données
        time.sleep(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AG-3 monitoring')
    parser.add_argument('json_file', type=str, help='Chemin vers le fichier JSON contenant les paramètres')
    parser.add_argument('-w', action='store_true', help='surveiller grille sans programme -w')
    args = parser.parse_args()

    with open(args.json_file) as f:
        params = json.load(f)

    if args.w:
        watchOnly = True
    main(params)
