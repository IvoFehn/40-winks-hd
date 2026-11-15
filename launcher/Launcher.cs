using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;

internal static class Launcher
{
    private const string RomHash = "899B866A45DFBEBC8152A3122F28AA0BA906FB448DC6B2DC7C7442E7622B5442";
    private static readonly string[] Resolutions = { "1080p", "1440p", "2160p" };
    private static readonly string[] Aspects = { "4:3", "16:9" };

    private static int Main()
    {
        Console.Title = "40 Winks HD";
        try
        {
            string root = AppDomain.CurrentDomain.BaseDirectory;
            string rom = FindRom(root);
            Console.WriteLine("40 Winks HD");
            Console.WriteLine("  1  Full HD (1920 x 1080)");
            Console.WriteLine("  2  WQHD (2560 x 1440)");
            Console.WriteLine("  3  4K UHD (3840 x 2160)");
            Console.WriteLine("  4  Native 4K rendering on any display");
            int mode = ReadChoice("Resolution", 4);
            Console.WriteLine("  1  4:3 original framing");
            Console.WriteLine("  2  16:9 widescreen");
            int aspect = ReadChoice("Aspect ratio", 2);
            return StartGame(root, rom, mode, Aspects[aspect - 1]);
        }
        catch (OperationCanceledException)
        {
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.Message);
            if (!Console.IsInputRedirected)
            {
                Console.WriteLine("Press Enter to close.");
                Console.ReadLine();
            }
            return 1;
        }
    }

    private static string FindRom(string directory)
    {
        foreach (FileInfo file in new DirectoryInfo(directory).EnumerateFiles("*.z64")
            .Where(item => item.Length == 32 * 1024 * 1024).OrderBy(item => item.Name, StringComparer.OrdinalIgnoreCase))
        {
            using (SHA256 sha = SHA256.Create())
            using (FileStream stream = file.OpenRead())
            {
                string hash = BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "");
                if (hash == RomHash)
                    return file.FullName;
            }
        }
        throw new FileNotFoundException("Put your 40 Winks N64 ROM beside this EXE. Use the European prototype dated 1999-10-07 in .z64 format.");
    }

    private static int ReadChoice(string prompt, int last)
    {
        while (true)
        {
            Console.Write(prompt + " [1-" + last + ", Enter for 1, Q to quit] ");
            string input = Console.ReadLine();
            if (input == null || input.Trim().Equals("q", StringComparison.OrdinalIgnoreCase))
                throw new OperationCanceledException();
            input = input.Trim();
            if (input.Length == 0)
                return 1;
            int choice;
            if (int.TryParse(input, out choice) && choice >= 1 && choice <= last)
                return choice;
        }
    }

    private static int StartGame(string root, string rom, int mode, string aspect)
    {
        string game = Path.Combine(root, "game");
        bool native4K = mode == 4;
        string script = Path.Combine(game, native4K ? "Play-4K.ps1" : "Play.ps1");
        if (!File.Exists(script))
            throw new FileNotFoundException("Extract the entire release ZIP before running the launcher.");
        string shell = Path.Combine(Environment.SystemDirectory, @"WindowsPowerShell\v1.0\powershell.exe");
        string args = "-NoLogo -NoProfile -ExecutionPolicy Bypass -File \"" + script
            + "\" -RomPath \"" + rom + "\" -Aspect " + aspect;
        if (!native4K)
            args += " -Resolution " + Resolutions[mode - 1];

        using (var session = new FileStream(Path.Combine(game, ".launcher.lock"), FileMode.OpenOrCreate,
            FileAccess.ReadWrite, FileShare.None))
        using (Process emulator = Process.Start(new ProcessStartInfo(shell, args)
        {
            UseShellExecute = false,
            WorkingDirectory = game
        }))
        {
            emulator.WaitForExit();
            if (emulator.ExitCode != 0)
                throw new InvalidOperationException("The game could not start or exited with an error. See the message above.");
            return 0;
        }
    }
}
