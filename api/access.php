<?php
// ini_set('display_errors', 1);
$config_base_url = "http://cgscomwww.catlin.edu/spanish/misterio/token/";
$City = "Toluca";

function die_error($code, $message) {
	// http_response_code($code);
	header(':', true, $code);
	echo json_encode(array('message' => $message));
	die();
}
if (!isset($req_admin) || ($req_admin !== TRUE && $req_admin !== FALSE)) {
	die_error(500, "Server Error: Access requirement not specified.");
}
if (isset($_GET['debugtoken'])) {
	$auth_token = $_GET['debugtoken'];
} else {
	$headers = apache_request_headers();
	if (!isset($headers["X-Session"])) {
		die_error(403, "No X-Session header.");
	}
	$auth_token = $headers["X-Session"];
}
$dbname = "spanish_mystery";
require("/home/web/spanish/dba.php");
$qry = $db->prepare("SELECT `UID`, `Name`, `Email`, `Admin` FROM `Players` WHERE `Token`=?");
if ($qry === FALSE
 || !$qry->bind_param("s", $auth_token)
 || !$qry->execute()
 || !$qry->bind_result($user_uid, $user_name, $user_email, $user_admin)) {
	die_error(500, "Server Error: Could not submit access query.");
}
if (!$qry->fetch()) {
	die_error(403, "No such token.");
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not finish access query.");
}
if ($req_admin && !$user_admin) {
	die_error(403, "Administrator access required.");
}
if (isset($get_json) && $get_json === TRUE) {
	$json_data = json_decode(file_get_contents('php://input'), true);
	if ($json_data === null) {
		die_error(400, "JSON required but not sent.");
	}
}
function generate_token() {
	return sha1(microtime(true).mt_rand(10000,90000).sha1(uniqid()));
}
function set_json() {
	header("Content-Type: application/json");
}
