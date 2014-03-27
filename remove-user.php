<?php
$req_admin = TRUE;
$get_json = FALSE;
require("access.php");
set_json();
if (!isset($_GET['uid'])) {
	die_error(400, "Should have id!");
}
$target_id = intval($_GET['uid']);
$qry = $db->prepare("SELECT `Email` FROM `Players` WHERE `UID`=?");
$old_email = NULL;
if ($qry === FALSE || !$qry->bind_param("i", $target_id) || !$qry->execute() || !$qry->bind_result($old_email)) {
	die_error(500, "Server Error: Could not submit prefix query.");
}
if (!$qry->fetch()) {
	die_error(400, "No such user!");
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not complete prefix query.");
}
$qry = $db->prepare("DELETE FROM `Players` WHERE `UID` = ?");
if ($qry === FALSE || !$qry->bind_param("i", $target_id) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
if ($old_email !== NULL && $old_email !== "") {
	mail($old_email, "Tu cuenta del Misterio en $City es borrada", "Tu cuenta del Misterio en $City es borrada ahora.\n", "From: $config_email_sender\r\n");
}
echo json_encode(array());
