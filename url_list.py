url_list = [
    "https://agriculture.canada.ca/fr/outils-gestion-risques-finances-agricoles",
    "https://agriculture.canada.ca/fr/programmes/paiements-directs-producteurs-laitiers",
    "https://agriculture.canada.ca/fr/production-agricole/lutte-antiparasitaire-agriculture/maladies-ravageurs-agroforesterie/punaise-lerable-negondo",
    "https://agriculture.canada.ca/fr/environnement/changements-climatiques/scenarios-climatiques-lagriculture",
    "https://agriculture.canada.ca/fr/science/systeme-canadien-dinformation-biodiversite-scib"
    "https://impact.canada.ca/fr/defis/defimethane",
    "https://agriculture.canada.ca/fr/outils-gestion-risques-finances-agricoles",
    "https://agriculture.canada.ca/fr/ministere/initiatives/sante-mentale",
    "https://agriculture.canada.ca/fr/ministere/initiatives/demarches-nationales-du-canada/document-demarches-nationales",
    "https://agriculture.canada.ca/fr/programmes/agri-stabilite/ressources/changements-importants-apportes-agri-stabilite-compter-lannee-programme-2024",
    "https://agriculture.canada.ca/fr/commerce-international",
    "https://agriculture.canada.ca/fr/science",
    "https://agriculture.canada.ca/fr/ministere/initiatives/politique-alimentaire",
    "https://agriculture.canada.ca/fr/programmes",
    "https://agriculture.canada.ca/fr/agri-info",
    "https://agriculture.canada.ca/fr/environnement",
    "https://agriculture.canada.ca/fr/jeunes",
    "https://agriculture.canada.ca/fr/peuples-autochtones",
    "https://agriculture.canada.ca/fr/ministere",
    "https://www.canada.ca/fr/agriculture-agroalimentaire/nouvelles/2023/12/les-gouvernements-du-canada-et-du-manitoba-elargissent-la-portee-du-programme-de-paysages-agricoles-resilients--sequestration-du-carbone-et-resilie.html",
    "https://www.canada.ca/fr/agriculture-agroalimentaire/nouvelles/2023/12/le-manitoba-signe-un-accord-de-contribution-pour-appuyer-la-construction-dune-installation-de-traitement-de-carburant-renouvelable.html",
    "https://www.canada.ca/fr/agriculture-agroalimentaire/nouvelles/2023/12/les-gouvernements-du-canada-et-de-la-saskatchewan-investissent-un-million-de-dollars-dans-le-cadre-dagri-relance-a-lappui-des-apiculteurs-touches-p.html",
    "https://agriculture.canada.ca/fr/nouvelles",
]

contents = get_content_from_url(url_list)

write_file("./agriculture_can.txt", "\n\n".join(contents))



    