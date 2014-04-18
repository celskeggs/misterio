<?php
$req_admin = TRUE;
require("access.php");
set_json();
if (!isset($_GET['be'])) {
	die_error(400, "No BE clause.");
}
$id = intval($_GET['be']);
if ($id === FALSE || $id < 1) {
	die_error(400, "Invalid BE clause.");
}
$qry = $db->prepare("SELECT `Token` FROM `Players` WHERE `UID`=?");
if ($qry === FALSE || !$qry->bind_param("i", $id) || !$qry->execute() || !$qry->bind_result($token) || !$qry->fetch() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
echo json_encode(array('target' => $token));
