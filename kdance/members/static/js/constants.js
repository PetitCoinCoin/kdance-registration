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
  '2': 'Le statut général des paiements',
  '3': 'Les chèques par mois',
  '4': 'La liste des Pass Sport',
  '5': 'La liste des licenciés',
  '6': 'Les contacts par cours',
  '7': 'Les contacts d\'urgence par cours',
}

const COMMON_TABLE_PARAMS = {
  locale: 'fr-FR',
  search: true,
  stickyHeader: true,
  showFullscreen: true,
  showColumns: true,
}

const DEFAULT_ERROR = 'Une erreur est survenue.';
const ERROR_SUFFIX = 'Veuillez ré-essayer plus tard ou contacter le support technique K\'Dance.';
const DEFAULT_ERROR_MESSAGE = `${DEFAULT_ERROR} ${ERROR_SUFFIX}`;
