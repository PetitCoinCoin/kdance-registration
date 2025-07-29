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

$(document).ready(() => {
	initialize();
});

async function initialize() {
	if (sessionStatus == 'SUCCESSFUL') {
		$('#checkout-success').attr('hidden', false);
		setTimeout(() => { location.href = '/'}, 7000);
	} else if (sessionStatus == 'STATUS_UNKNOWN') {
		$('#checkout-unknown').attr('hidden', false);
		setTimeout(() => { location.href = '/'}, 10000);
	} else {
		$('#checkout-failure').attr('hidden', false);
		setTimeout(() => { location.href = '/checkout'}, 7000);
	}
}
