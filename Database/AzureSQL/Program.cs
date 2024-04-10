using DbUp;
using DbUp.Builder;
using DbUp.Engine;
using DbUp.ScriptProviders;
using DbUp.Helpers;
using DbUp.Support;
using System;
using System.IO;
using System.Reflection;

namespace AzureSQLDevelopers.Database.Deploy {
  class Program {
    static int Main(string[] args) {
      DotNetEnv.Env.Load();

      Console.WriteLine("Get variables from workflow. - START");
      var SAImplementationConnStr = Environment.GetEnvironmentVariable("SAImplementation");
      var MetadataConnStr = Environment.GetEnvironmentVariable("SAMetadata");
      var SAOpConnStr = Environment.GetEnvironmentVariable("SAOp");
      var chgHistSchema = "dbo";
      var chgHistTable = "TBL_GIT_CHANGE_HISTORY";
      Console.WriteLine("Get variables from workflow. - DONE");

      Console.WriteLine("ENABLE IncludeSubDirectories");
      var fsso = new FileSystemScriptOptions();
      fsso.IncludeSubDirectories = true;

      Console.WriteLine("Run SQL Scripts from SAImplementation. - START");
      var versionedUpgraderA = DeployChanges.To
        .SqlDatabase(SAImplementationConnStr)
        .JournalToSqlTable(chgHistSchema, chgHistTable)
        .WithScriptsFromFileSystem("./SAImplementation/versioned_sql", fsso)
        .LogToConsole()
        .Build();

      var firstResultA = versionedUpgraderA.PerformUpgrade();

      if (!firstResultA.Successful) {
        Console.WriteLine(firstResultA.Error);
        return -1;
      }

      var alwaysUpgraderA = DeployChanges.To
        .SqlDatabase(SAImplementationConnStr)
        .WithScriptsFromFileSystem("./SAImplementation/always_sql", fsso)
        .JournalTo(new NullJournal())
        .LogToConsole()
        .Build();

      var secondResultA = alwaysUpgraderA.PerformUpgrade();

      if (!secondResultA.Successful) {
        Console.WriteLine(secondResultA.Error);
        return -1;
      }
      Console.WriteLine("Run SQL Scripts from SAImplementation. - DONE");

      Console.WriteLine("Run SQL Scripts from SAMetadata. - START");
      var alwaysUpgraderB = DeployChanges.To
        .SqlDatabase(MetadataConnStr)
        .WithScriptsFromFileSystem("./SAMetadata/always_sql", fsso)
        .JournalTo(new NullJournal())
        .LogToConsole()
        .Build();

      var firstResultB = alwaysUpgraderB.PerformUpgrade();

      if (!firstResultB.Successful) {
        Console.WriteLine(firstResultB.Error);
        return -1;
      }
      Console.WriteLine("Run SQL Scripts from SAMetadata. - DONE");

      Console.WriteLine("Run SQL Scripts from SAOp. - START");
      var versionedUpgraderC = DeployChanges.To
        .SqlDatabase(SAOpConnStr)
        .JournalToSqlTable(chgHistSchema, chgHistTable)
        .WithScriptsFromFileSystem("./SAOp/versioned_sql", fsso)
        .LogToConsole()
        .Build();

      var firstResultC = versionedUpgraderC.PerformUpgrade();

      if (!firstResultC.Successful) {
        Console.WriteLine(firstResultC.Error);
        return -1;
      }
      Console.WriteLine("Run SQL Scripts from SAOp. - DONE");

      Console.WriteLine("Success!");
      return 0;
    }
  }
}
