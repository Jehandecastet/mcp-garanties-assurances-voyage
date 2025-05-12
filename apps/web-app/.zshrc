
# This line enable prompt to track the right branch for git
autoload -Uz vcs_info
precmd() { vcs_info }
setopt PROMPT_SUBST
PS1='%n@%m:%~${vcs_info_msg_0_}%# '

# This line to create an alias for python3
alias python="python3"



# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/Jehan/Downloads/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/Jehan/Downloads/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/Jehan/Downloads/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/Jehan/Downloads/google-cloud-sdk/completion.zsh.inc'; fi

# The next line enables shell command completion for Nodejs
export PATH="$PATH:/usr/local/bin"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
export PATH=$PATH:/Users/Jehan/.nvm/versions/node/v22.14.0/bin

