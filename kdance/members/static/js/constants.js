/************************************************************************************/
/* Copyright 2024, 2025 Andréa Marnier                                              */
/*                                                                                  */
/* This file is part of KDance registration.                                        */
/*                                                                                  */
/* KDance registration is free software: you can redistribute it and/or modify it   */
/* under the terms of the GNU Affero General Public License as published by the     */
/* Free Software Foundation, either version 3 of the License, or any later version. */
/*                                                                                  */
/* KDance registration is distributed in the hope that it will be useful, but       */
/* WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or    */
/* FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License      */
/* for more details.                                                                */
/*                                                                                  */
/* You should have received a copy of the GNU Affero General Public License along   */
/* with KDance registration. If not, see <https://www.gnu.org/licenses/>.           */
/************************************************************************************/

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
const CONTACT_NUMBER = 2;

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
