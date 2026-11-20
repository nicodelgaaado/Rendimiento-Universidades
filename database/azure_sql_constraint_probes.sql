DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; INSERT INTO [rendimiento].[DimensionTemas] SELECT TOP (1) * FROM [rendimiento].[DimensionTemas]; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51101, 'Duplicate primary key accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosObservaciones] SET [IdTema]=999999 WHERE [IdObservacion]=1; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51102, 'Orphan foreign key accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosObservaciones] SET [CategoriaRendimiento]=N'X' WHERE [IdObservacion]=1; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51103, 'Invalid category accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosObservaciones] SET [VecesManoLevantada]=-1 WHERE [IdObservacion]=1; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51104, 'Negative activity accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosNotasOficiales] SET [PromedioNotaPublicado]=6; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51105, 'Grade outside scale accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosNotasOficiales] SET [Inscritos]=[Inscritos]+1; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51106, 'Inconsistent grade counts accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosNotasOficiales] SET [PromedioNotaParaAnalisis]=0 WHERE [PromedioNotaPublicado]=0; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51107, 'Invalid analysis zero accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosDesercionOficial] SET [DesertoresNetos]=[DesertoresNetos]+1; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51108, 'Inconsistent dropout count accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosDesercionOficial] SET [PeriodoSeguimiento]=N'2099-1'; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51109, 'Mismatched follow-up period accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; DELETE FROM [rendimiento].[DimensionTemas]; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51110, 'Referenced dimension deletion accepted', 1;
GO
DECLARE @accepted bit = 0;
BEGIN TRY BEGIN TRAN; UPDATE [rendimiento].[HechosObservaciones] SET [Genero]=NULL WHERE [IdObservacion]=1; SET @accepted=1; ROLLBACK; END TRY BEGIN CATCH IF XACT_STATE()<>0 ROLLBACK; END CATCH;
IF @accepted=1 THROW 51111, 'Required NULL accepted', 1;
GO
