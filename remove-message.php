<?php
$req_admin = TRUE;
$get_json = FALSE;
require("access.php");
set_json();
if (!isset($_GET['id'])) {
	die_error(400, "Should have id!");
}
$target_id = intval($_GET['id']);
$qry = $db->prepare("DELETE FROM `Posts` WHERE `UID` = ?");
if ($qry === FALSE || !$qry->bind_param("i", $target_id) || !$qry->execute() || !$qry->close()) {
	die_error(500, "Server Error: Could not submit body query.");
}
echo json_encode(array());
