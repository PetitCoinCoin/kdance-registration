const WEEKDAY = {
  0: 'Lundi',
  1: 'Mardi',
  2: 'Mercredi',
  3: 'Jeudi',
  4: 'Vendredi',
  5: 'Samedi',
  6: 'Dimanche',
}

const MONTH = {
  0: 'Sélectionner...',
  1: 'Janvier',
  2: 'Février',
  3: 'Mars',
  4: 'Avril',
  10: 'Octobre',
  11: 'Novembre',
}

const LICENSES = {
  0: 'Aucune',
  19: 'Licence A Loisir',
  21: 'Licence B Compétiteur',
  38: 'Licence C Compétiteur national',
  50: 'Licence D Compétiteur international',
}

const CHECK_NUMBER = 8;
const CONTACT_CUSTOM_NUMBER = 2;
const CONTACT_ALL_NUMBER = CONTACT_CUSTOM_NUMBER + 1; // Plus user

const CONTACT_MAPPING = {
  'responsible': 'Responsable légal',
  'emergency': 'Contact d\'urgence',
}

const LIST_MAIN_MAPPING = {
  '0': '...',
  '1': 'Les adhérents par cours',
  '2': 'Les chèques par mois',
  '3': 'La liste des Pass Sport',
  '4': 'La liste des licenciés',
}

const COMMON_TABLE_PARAMS = {
  locale: 'fr-FR',
  search: true,
  stickyHeader: true,
  showFullscreen: true,
  showColumns: true,
}