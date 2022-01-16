-- MySQL dump 10.13  Distrib 8.0.26, for macos11.3 (x86_64)
--
-- Host: 192.168.88.101    Database: CardFillingBot
-- ------------------------------------------------------
-- Server version	5.5.5-10.6.5-MariaDB-1:10.6.5+maria~focal

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `card_fill`
--

DROP TABLE IF EXISTS `card_fill`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `card_fill` (
  `fill_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `fill_date` datetime NOT NULL,
  `amount` float NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `category_code` varchar(255) DEFAULT 'OTHER',
  PRIMARY KEY (`fill_id`),
  KEY `user_id` (`user_id`),
  KEY `category_code` (`category_code`),
  CONSTRAINT `card_fill_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `telegram_user` (`user_id`),
  CONSTRAINT `card_fill_ibfk_2` FOREIGN KEY (`category_code`) REFERENCES `category` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=501 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `category`
--

DROP TABLE IF EXISTS `category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `category` (
  `code` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `aliases` text NOT NULL DEFAULT '',
  `proportion` decimal(3,2) NOT NULL DEFAULT 1.00,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `monthly_report`
--

DROP TABLE IF EXISTS `monthly_report`;
/*!50001 DROP VIEW IF EXISTS `monthly_report`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `monthly_report` AS SELECT 
 1 AS `rownumber`,
 1 AS `username`,
 1 AS `fill_year`,
 1 AS `month_num`,
 1 AS `amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `monthly_report_by_category`
--

DROP TABLE IF EXISTS `monthly_report_by_category`;
/*!50001 DROP VIEW IF EXISTS `monthly_report_by_category`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `monthly_report_by_category` AS SELECT
 1 AS `rownumber`,
 1 AS `username`,
 1 AS `fill_year`,
 1 AS `month_num`,
 1 AS `category_name`,
 1 AS `amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `monthly_report_v2`
--

DROP TABLE IF EXISTS `monthly_report_v2`;
/*!50001 DROP VIEW IF EXISTS `monthly_report_v2`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `monthly_report_v2` AS SELECT
 1 AS `rownumber`,
 1 AS `fill_month`,
 1 AS `kuznetsov_na`,
 1 AS `askrasnova`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `telegram_user`
--

DROP TABLE IF EXISTS `telegram_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `telegram_user` (
  `user_id` int(11) NOT NULL,
  `is_bot` tinyint(1) NOT NULL,
  `first_name` varchar(255) DEFAULT NULL,
  `last_name` varchar(255) DEFAULT NULL,
  `username` varchar(255) DEFAULT NULL,
  `language_code` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Final view structure for view `monthly_report`
--

/*!50001 DROP VIEW IF EXISTS `monthly_report`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `monthly_report` AS select row_number() over ( partition by NULL order by NULL) AS `rownumber`,`tuser`.`username` AS `username`,year(`cf`.`fill_date`) AS `fill_year`,month(`cf`.`fill_date`) AS `month_num`,sum(`cf`.`amount`) AS `amount` from (`card_fill` `cf` join `telegram_user` `tuser` on(`tuser`.`user_id` = `cf`.`user_id`)) group by `tuser`.`username`,year(`cf`.`fill_date`),month(`cf`.`fill_date`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `monthly_report_by_category`
--

/*!50001 DROP VIEW IF EXISTS `monthly_report_by_category`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `monthly_report_by_category` AS select row_number() over ( partition by NULL order by NULL) AS `rownumber`,`tuser`.`username` AS `username`,year(`cf`.`fill_date`) AS `fill_year`,month(`cf`.`fill_date`) AS `month_num`,`cat`.`name` AS `category_name`,sum(`cf`.`amount`) AS `amount` from ((`card_fill` `cf` join `telegram_user` `tuser` on(`tuser`.`user_id` = `cf`.`user_id`)) join `category` `cat` on(`cat`.`code` = `cf`.`category_code`)) group by `tuser`.`username`,year(`cf`.`fill_date`),month(`cf`.`fill_date`),`cat`.`name` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `monthly_report_v2`
--

/*!50001 DROP VIEW IF EXISTS `monthly_report_v2`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `monthly_report_v2` AS select row_number() over ( partition by NULL order by NULL) AS `rownumber`,concat(concat(cast(year(`cf`.`fill_date`) as char(4) charset utf8mb4),'-'),cast(month(`cf`.`fill_date`) as char(2) charset utf8mb4)) AS `fill_month`,sum(coalesce(case when `tuser`.`user_id` = 86070242 then `cf`.`amount` else 0 end,0)) AS `kuznetsov_na`,sum(coalesce(case when `tuser`.`user_id` = 426827557 then `cf`.`amount` else 0 end,0)) AS `askrasnova` from (`card_fill` `cf` join `telegram_user` `tuser` on(`tuser`.`user_id` = `cf`.`user_id`)) group by year(`cf`.`fill_date`),month(`cf`.`fill_date`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-01-05 18:25:13
