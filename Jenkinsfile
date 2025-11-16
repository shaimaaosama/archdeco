pipeline {
  agent any

  environment {
    HOST = "157.175.78.253"
    USER = "admin"
    SERVICE = "systemctl restart odoo18"
    CREDID = "arch18"
    ADDONS = "/opt/odoo18/custom-addons"
    GITREPO = "ptech-sh/archdeco18.git"
  }

stages {
    stage("Remote SSH") {
      steps {
        script {
            withCredentials([usernameColonPassword(credentialsId: 'ShorbagiGit', variable: 'USERPASS')]) {
              withCredentials([sshUserPrivateKey(credentialsId: "${CREDID}", keyFileVariable: 'key')]) {
                def remote = [name: "${HOST}", host: "${HOST}", user: "${USER}", allowAnyHosts: true, identityFile: key]
                sshCommand remote: remote, sudo: true, command: "git -C ${ADDONS} pull https://$USERPASS@github.com/${GITREPO}"
                sshCommand remote: remote, sudo: true, command: "${SERVICE}"
            }
          }
        }
      }
    }
    stage('Check website is up') {
        steps {
                echo 'Check website is up'
                sh 'curl -Is ${HOST} | head -n 1'
            }
        }
  }
}
