import requests
import time
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from rich import box
import schedule

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
    zones = zones["zones"]

    # Ajouter les colonnes pour chaque zone
    for zone_id in range(taille):
        table.add_column(str(zone_id), justify="center")

    # Ajouter les lignes pour chaque secteur
    for secteur_id in range(taille):
        row_data = []
        for zone_id in range(taille):
            zone = next((z for z in zones if z["secteur_id"] == secteur_id and z["zone_id"] == zone_id), None)
            if zone is not None:
                if not zone["status"]:
                    row_data.append("[red]N[/red]")
                elif zone["actif"]:
                    row_data.append("[green]X[/green]")
                else:
                    row_data.append("[blue]S[/blue]")
            else:
                row_data.append(" ")
        table.add_row(*row_data)
    return table

def refresh_grids():
    console = Console(style="default")
    # Faire une requête HTTP pour obtenir l'objet JSON pour la première grille
    response1 = requests.get('http://localhost/v1/grid')
    data1 = response1.json()

    # Générer la première grille
    table1 = generate_grid(data1)

    # Faire une requête HTTP pour obtenir l'objet JSON pour la deuxième grille
    response2 = requests.get('http://localhost/v1/grid')
    data2 = response2.json()

    # Générer la deuxième grille
    table2 = generate_grid(data2)

    console.clear()  # Effacer l'écran

    # Afficher les deux grilles côte à côte
    console.print(Columns([table1, table2]))

    # Faire une requête HTTP pour obtenir l'objet JSON
    response = requests.get('http://localhost/v1/programme/infos/8999c3c008742c9c0b672d3ca0c7830d9035da4a/264f2a34bbccf874f6dc3c67cc87d6224c4af03e')
    programme_data = response.json()
    programme_tab = generate_tables(programme_data)
    console.print(programme_tab)



schedule.every(5).seconds.do(refresh_grids)

while True:
    schedule.run_pending()
    # Attendre 5 secondes avant de mettre à jour les données
    time.sleep(5)
