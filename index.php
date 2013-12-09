<?php
error_reporting(E_ALL);
ini_set("display_errors", "stdout");
$req_access = 1;
require('begin.php');
$pqry = $db->prepare("SELECT `IsPublic`,`Date`,`Contents`,`Name`,`Avatar` FROM `Posts`,`Players` WHERE `Author`=`Players`.`UID` AND (`IsPublic` = 1 OR `Author`=?) ORDER BY `Date` DESC");
$pqry->bind_param("i", $userid);
$pqry->execute();
$pqry->bind_result($qry_ispublic, $qry_date, $qry_contents, $qry_author, $qry_avatar);
$posts = array();
while ($pqry->fetch()) {
	$posts[] = array($qry_ispublic, $qry_date, $qry_contents, $qry_author, $qry_avatar);
}
$pqry->close();
require('header.php');
?>
    <div id="title">
      Bienvenidos al Misterio en Cuzco,
      <?php echo htmlentities($username) . ".";
        if ($admin_access) {
      ?>
        <a href='profesor.php'>Ir a la pachina del profesor</a>
      <?php
        }
      ?>
    </div>
    <div id="content">
<?php
if (count($posts) > 0) {
?>
    <ul id="posts">
    <li class="post new-post">
      <img class="avatar" src="<?php echo $useravatar; ?>" alt="Avatar" />
      <div class="contents"><div class="author"><?php echo htmlentities($username); ?></div><div class="body"><textarea id="editpost"> </textarea></div></div>
    </li>
<?php
	foreach ($posts as $post) {
		$postclasses = array("post");
		$ispublic = $post[0];
		if (!$ispublic) {
			$postclasses[] = "private";
		}
		$date = $post[1];
		$contents = $post[2];
		$author = $post[3];
		$avatar = str_replace("'", urlencode("'"), str_replace('"', urlencode('"'), $post[4]));
?>
    <li class="<?php echo implode(' ', $postclasses); ?>">
      <img class="avatar" src="<?php echo $avatar; ?>" alt="Avatar" />
      <div class="contents"><div class="author"><?php echo htmlentities($author); ?></div><div class="body"><?php echo htmlentities($contents); ?></div></div>
    </li>
<?php
	}
}
?>
    <div id="noposts">No hay m&aacute;s postes</div>
    </ul>
    </div>
<?php
  require('footer.php');
?>
