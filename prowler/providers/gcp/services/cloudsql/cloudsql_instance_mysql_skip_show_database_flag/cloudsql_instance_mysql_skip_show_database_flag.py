from prowler.lib.check.models import Check, Check_Report_GCP
from prowler.providers.gcp.services.cloudsql.cloudsql_client import cloudsql_client


class cloudsql_instance_mysql_skip_show_database_flag(Check):
    def execute(self) -> Check_Report_GCP:
        findings = []
        for instance in cloudsql_client.instances:
            if "MYSQL" in instance.version:
                report = Check_Report_GCP(metadata=self.metadata(), resource=instance)
                report.status = "FAIL"
                report.status_extended = f"MySQL Instance {instance.name} does not have 'skip_show_database' flag set to 'on'."
                for flag in instance.flags:
                    if (
                        flag.get("name", "") == "skip_show_database"
                        and flag.get("value", "off") == "on"
                    ):
                        report.status = "PASS"
                        report.status_extended = f"MySQL Instance {instance.name} has 'skip_show_database' flag set to 'on'."
                        break
                findings.append(report)

        return findings
