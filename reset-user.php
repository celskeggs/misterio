<?php
$req_admin = TRUE;
$get_json = FALSE;
require("access.php");
set_json();
if (!isset($_GET['uid'])) {
	die_error(400, "Should have id!");
}
$target_id = intval($_GET['uid']);
$new_token = generate_token();
$qry = $db->prepare("SELECT `Email` FROM `Players` WHERE `UID`=?");
$target_email = NULL;
if ($qry === FALSE || !$qry->bind_param("i", $target_id) || !$qry->execute() || !$qry->bind_result($target_email)) {
	die_error(500, "Server Error: Could not submit prefix query.");
}
if (!$qry->fetch()) {
	die_error(400, "No such user!");
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not complete prefix query.");
}
if ($target_email === NULL || $target_email === "") {
	die_error(400, "This user has no email, and thusly cannot have a token.");
}
$qry = $db->prepare("UPDATE `Players` SET `Token` = ? WHERE `UID` = ?");
if ($qry === FALSE || !$qry->bind_param("si", $new_token, $target_id) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
mail($new_email, "Tu cuenta del Misterio en $City", "Tu cuenta del Misterio en $City tiene un enlace nuevo para entrar: " . $config_base_url . $new_token . "\n");
echo json_encode(array());
